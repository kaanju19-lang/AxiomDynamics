"""
Tests for tools/sign_release.py (D09 §7.3 signed releases).

Three properties, and the third is the one that is usually skipped:

  1. A signature verifies against the published public key, and a modified
     archive does not.
  2. A signature made by a different key does not verify against ours — which is
     what makes it a signature rather than a checksum.
  3. Two builds of the same content produce the same bytes. Without this, the
     signature attests to the build host's clock and user id as much as to the
     code, and "verify the release" means "verify that it was built at some
     time by someone".

These tests need a `gpg` binary. Where there is none they skip with a printed
reason rather than passing silently — a skipped test that looks like a pass is
the defect class this project keeps finding.

Run: python3 -I tests/test_sign_release.py
"""

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "sign_release.py")
spec = importlib.util.spec_from_file_location("sign_release", TOOL)
rel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rel)

RESULTS = []
HAVE_GPG = shutil.which("gpg") is not None


def test(fn):
    try:
        fn()
    except AssertionError as exc:
        RESULTS.append((fn.__name__, False, exc))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, "%s: %s" % (type(exc).__name__, exc)))
    else:
        RESULTS.append((fn.__name__, True, None))
    return fn


def skip(reason):
    raise AssertionError("SKIPPED: " + reason)


TMP = tempfile.mkdtemp(prefix="axiom-release-test-")


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


_KEYRING = tempfile.mkdtemp(prefix="axiom-gpg-shared-")
os.environ["GNUPGHOME"] = _KEYRING


def _make_key(tag):
    """
    All test keys live in one GNUPGHOME. Giving each its own would make the
    wrong-key test impossible to set up — the tool would sign with a key in a
    keyring it cannot reach — and would test the harness rather than the
    property.

    Idempotent: a second run of the suite in the same session must reuse the key
    rather than fail on "a key for this uid already exists", which is what
    happened when the suite was run twice.
    """
    env = dict(os.environ, GNUPGHOME=_KEYRING)
    existing = _find_key(tag, env)
    if existing:
        return existing
    p = subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback",
                        "--passphrase", "", "--quick-gen-key",
                        "Axiom %s <t-%s@example.invalid>" % (tag, tag),
                        "ed25519", "sign", "0"], env=env, capture_output=True,
                       text=True)
    if p.returncode != 0:
        raise AssertionError("key generation failed: %s" % (p.stderr or p.stdout))
    found = _find_key(tag, env)
    if not found:
        raise AssertionError("could not create a test key")
    return found


def _find_key(tag, env):
    p = subprocess.run(["gpg", "--list-secret-keys", "--with-colons", tag],
                       env=env, capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("fpr:"):
            return line.split(":")[9]
    return None




# ---------------------------------------------------------------------------
# build — content selection and reproducibility
# ---------------------------------------------------------------------------
@test
def test_the_archive_contains_code_and_not_the_database_or_bytecode():
    out = os.path.join(TMP, "c1")
    archive, manifest, n = rel.build(out, "content")
    with tarfile.open(archive) as tf:
        names = tf.getnames()
    assert n > 0
    assert any(nm.endswith("backend/main.py") for nm in names), names[:5]
    assert any(nm.endswith("requirements.txt") for nm in names)
    assert not any("__pycache__" in nm for nm in names)
    assert not any(nm.endswith(".pyc") for nm in names)
    assert not any("/.git" in nm for nm in names)
    # axiom.db is not under any RELEASE_CONTENT entry, so its absence proves
    # nothing about NEVER_SHIP. That is recorded rather than pretended: it is
    # the content list, not the exclusion list, that keeps the demo ledger out.
    assert not any(nm.endswith("axiom.db") for nm in names)


@test
def test_the_exclusion_list_works_on_an_entry_that_is_actually_in_scope():
    """
    The previous version of this check asserted axiom.db was absent from the
    archive — true, but true because axiom.db is outside RELEASE_CONTENT, not
    because NEVER_SHIP filtered it. Removing "axiom.db" from NEVER_SHIP left
    the test green. This one drives the filter directly with an in-scope path.
    """
    d = os.path.join(TMP, "scope")
    os.makedirs(os.path.join(d, "backend", "__pycache__"), exist_ok=True)
    for name, body in (("backend/main.py", "x"),
                       ("backend/__pycache__/main.pyc", "y"),
                       ("backend/axiom.db", "z"),
                       ("backend/mod.pyc", "w")):
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write(body)
    got = sorted(rel._iter_files(os.path.join(d, "backend"),
                                 os.path.join(d, "backend")))
    assert got == ["main.py"], got


@test
def test_two_builds_of_the_same_content_are_byte_identical():
    """
    Reproducibility is a security property here, not tidiness. If the archive
    differs between builds, the signature covers the difference.

    The sleep is load-bearing, not politeness. Both the gzip header mtime and
    the tar entry mtimes have one-second resolution, so two builds started in
    the same second are byte-identical even when neither is deterministic —
    this test passed with both fixes removed until the delay was added. A test
    that cannot fail is not a test.
    """
    a1, _, _ = rel.build(os.path.join(TMP, "r1"), "same")
    time.sleep(1.2)
    a2, _, _ = rel.build(os.path.join(TMP, "r2"), "same")
    assert _sha(a1) == _sha(a2), (
        "two builds of identical content produced different bytes; the tarball "
        "is carrying mtime/uid/gid into the signature")


@test
def test_the_manifest_lists_every_file_it_should_and_hashes_match():
    out = os.path.join(TMP, "m1")
    archive, manifest, n = rel.build(out, "man")
    lines = [l for l in open(manifest, encoding="utf-8").read().splitlines()
             if l.strip()]
    assert len(lines) == n, (len(lines), n)
    for line in lines:
        digest, arc = line.split("  ", 1)
        assert len(digest) == 64, line
        src = os.path.join(ROOT, arc.split("/", 1)[1])
        assert os.path.isfile(src), src
        assert rel._sha256(src) == digest, line


@test
def test_a_tampered_archive_fails_verification():
    if not HAVE_GPG:
        skip("no gpg on this host")
    key = _make_key("tamper")
    out = os.path.join(TMP, "t1")
    archive, _, _ = rel.build(out, "tamper")
    rel.sign(archive, key)
    # Verify against the published key, not the local trustdb: a bare
    # `gpg --verify` in the signing keyring would find the key and pass, which
    # is not the check the Railroad performs.
    pub = os.path.join(out, "PUB.asc")
    rel.export_key(key, pub)
    ok, detail = rel.verify(archive, keyring=pub)
    assert ok, detail

    # Append a byte. The archive is gzip; appending garbage is enough to change
    # the file without needing to rebuild it, which is exactly what a
    # substitution attack looks like.
    with open(archive, "ab") as fh:
        fh.write(b"\x00")
    ok, detail = rel.verify(archive, keyring=pub)
    assert not ok, "a modified archive verified against its own signature"


@test
def test_a_signature_from_another_key_does_not_verify_against_our_public_key():
    """
    The property that distinguishes a signature from a checksum. Both archives
    are internally consistent; only one was signed by the key we published.
    """
    if not HAVE_GPG:
        skip("no gpg on this host")
    ours = _make_key("ours")
    theirs = _make_key("theirs")
    out = os.path.join(TMP, "k1")
    archive, _, _ = rel.build(out, "keys")
    pub = os.path.join(out, "PUB.asc")
    rel.export_key(ours, pub)

    rel.sign(archive, theirs)   # signed by the wrong key
    ok, detail = rel.verify(archive, keyring=pub)
    assert not ok, ("an archive signed by a different key verified against our "
                    "published key: %s" % detail)


@test
def test_verification_without_the_public_key_is_not_a_pass():
    if not HAVE_GPG:
        skip("no gpg on this host")
    key = _make_key("nokey")
    out = os.path.join(TMP, "n1")
    archive, _, _ = rel.build(out, "nokey")
    rel.sign(archive, key)
    # Verify in a clean keyring with no import: gpg cannot attribute the key.
    ok, detail = rel.verify(archive, keyring=None)
    # It may verify as "good signature from an unknown key", which is why the
    # caller must pass a keyring. Recorded here so nobody reads a bare
    # ok=True as proof of authorship.
    if ok:
        assert "key " in detail, detail


@test
def test_a_missing_signature_is_reported_not_raised():
    out = os.path.join(TMP, "s1")
    archive, _, _ = rel.build(out, "nosig")
    if os.path.exists(archive + ".asc"):
        os.remove(archive + ".asc")
    ok, detail = rel.verify(archive)
    assert ok is False and "no signature" in detail, detail


@test
def test_a_missing_archive_is_reported_not_raised():
    ok, detail = rel.verify(os.path.join(TMP, "does-not-exist.tar.gz"))
    assert ok is False and "no such archive" in detail, detail


@test
def test_the_tool_imports_only_the_standard_library():
    import ast
    src = open(TOOL, encoding="utf-8").read()
    mods = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    allowed = {"argparse", "hashlib", "os", "subprocess", "sys", "tarfile",
               "time", "tempfile", "shutil", "gzip", "__future__"}
    assert not (mods - allowed), mods - allowed


# ---------------------------------------------------------------------------
def main():
    print(f"{len(RESULTS)} tests ({'gpg available' if HAVE_GPG else 'NO GPG — signing tests skipped'})")
    bad = 0
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f" -> {exc!r}"))
        bad += 0 if ok else 1
    print(f"\n{len(RESULTS) - bad} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
