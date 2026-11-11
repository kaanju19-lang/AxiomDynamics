"""
Build, sign and verify a release artefact (D09 §7.3, §4.4 target Q2 2027).

D09 §7.3 says, in bold, that Supplier does not sign release artefacts. This
changes that from a statement about us to a statement about a tool, and the
distinction the section already draws is the one this module keeps: **a release
signature and a ledger-export signature are different things.**

  * The ledger export signs DATA produced on the Railroad's host, with a
    symmetric key, so any verifier can also forge. §4.5a.
  * A release signs a BUILD we ship, with an asymmetric key, so a verifier can
    check authorship without being able to produce it. That is the whole reason
    to use GPG here rather than the HMAC the export uses: the export's threat is
    a Railroad insider changing a disposition; the release's threat is anybody
    between us and the Railroad substituting a tarball.

**Why this wraps `gpg` instead of implementing anything.** D09 §7.3 promises a
GPG key and a published public key; the Railroad's own security team already
knows how to check `gpg --verify`, and a bespoke scheme would ask them to learn
ours. The same principle as `tools/verify_ledger_export.py` importing nothing: a
recipient must be able to verify us with tools they already trust.

**What the signature does not prove, stated here because it will be asked.**
A valid signature proves the artefact was signed by the private key and has not
changed since. It does not prove the key was ours unless the public key reached
the Railroad by a path they trust, and it does not prove the build is free of a
defect, only that it is the build we signed. Those limits go in §7.3, not in a
footnote.

Usage:
    python3 -I tools/sign_release.py build   --out DIR [--label NAME]
    python3 -I tools/sign_release.py sign    --archive FILE [--key FPR]
    python3 -I tools/sign_release.py verify  --archive FILE --keyring PUB.asc
    python3 -I tools/sign_release.py export-key --key FPR --out PUB.asc

`build` produces a deterministic tarball plus a MANIFEST.sha256 that C01 Part C2
already describes, so the sealed-archive path gains a signature without gaining
a new procedure.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tarfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What goes into a release. Deliberately a fixed list rather than "everything
# that is not ignored": a release that picks up whatever happens to be in the
# working tree is not a release, it is a snapshot, and nobody can reconstruct
# which snapshot the Railroad is running. This list is the same set the
# Dockerfile copies, so the two cannot drift without someone noticing.
RELEASE_CONTENT = ("backend", "frontend", "tests", "tools", "requirements.txt")

# Never shipped. Listed rather than filtered implicitly so that a future
# addition to the tree is a visible omission review, not a silent inclusion.
NEVER_SHIP = (".git", "__pycache__", ".pytest_cache", "axiom.db", ".env",
              "node_modules", ".venv", "venv")

_SKIP_SUFFIX = (".pyc", ".pyo")


def _iter_files(path, base):
    for name in sorted(os.listdir(path)):
        if name in NEVER_SHIP:
            continue
        full = os.path.join(path, name)
        if os.path.isdir(full):
            yield from _iter_files(full, base)
        elif os.path.isfile(full) and not full.endswith(_SKIP_SUFFIX):
            yield os.path.relpath(full, base).replace(os.sep, "/")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalise(info):
    """
    Strip the things that make a tarball non-reproducible.

    Two builds of identical content should produce identical bytes, or the
    signature over the archive attests to the build machine's clock and user id
    as much as to the code. mtime is pinned to the same instant for the same
    reason: a source tree checked out twice has two different mtimes and the
    same content.
    """
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    info.mtime = 1767225600  # 2026-01-01T00:00:00Z, fixed
    info.mode = 0o644 if not info.isdir() else 0o755
    return info


def build(out_dir, label):
    os.makedirs(out_dir, exist_ok=True)
    name = "axiomdynamics-%s.tar.gz" % label
    archive = os.path.join(out_dir, name)

    picked = []
    for entry in RELEASE_CONTENT:
        full = os.path.join(ROOT, entry)
        if os.path.isfile(full):
            picked.append((full, os.path.join("AxiomDynamics", entry)))
        elif os.path.isdir(full):
            for rel in _iter_files(full, ROOT):
                picked.append((os.path.join(ROOT, rel),
                               os.path.join("AxiomDynamics", rel)))
    if not picked:
        raise SystemExit("nothing to release — RELEASE_CONTENT found no files")

    # Deterministic ordering.
    picked.sort(key=lambda p: p[1])

    # The gzip container carries its own mtime in the header, independent of
    # the mtimes inside the tar. `tarfile.open(..., "w:gz")` writes the current
    # time into those four bytes, so two builds a second apart differ while
    # their contents are identical — and the signature would cover the
    # difference. Writing the gzip header ourselves with mtime=0 is the only
    # way to pin it without a third-party library.
    import gzip
    with open(archive, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                           mtime=0, compresslevel=9) as gz:
            with tarfile.open(fileobj=gz, mode="w",
                              format=tarfile.GNU_FORMAT) as tf:
                for src, arc in picked:
                    info = tf.gettarinfo(src, arcname=arc)
                    if info is None:
                        continue
                    _normalise(info)
                    with open(src, "rb") as fh:
                        tf.addfile(info, fh)

    # The manifest C01 Part C2 already expects, written beside the archive.
    lines = []
    for src, arc in picked:
        lines.append("%s  %s" % (_sha256(src), arc))
    manifest = os.path.join(out_dir, "MANIFEST.sha256")
    with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    return archive, manifest, len(picked)


def _gpg(args, **kw):
    return subprocess.run(["gpg", "--batch", "--yes"] + args,
                          capture_output=True, text=True, **kw)


def sign(archive, key=None):
    sig = archive + ".asc"
    args = ["--armor", "--detach-sign", "--output", sig]
    if key:
        args += ["--local-user", key]
    args.append(archive)
    p = _gpg(args)
    if p.returncode != 0:
        raise SystemExit("signing failed: %s" % (p.stderr or p.stdout).strip())
    return sig


def verify(archive, keyring=None, sig=None):
    """
    Return (ok, detail). Verifying against a provided public key rather than the
    local trustdb is the point: the Railroad does not have our key in their
    keyring, and an import into a shared keyring is a side effect nobody asked
    for.
    """
    sig = sig or (archive + ".asc")
    if not os.path.isfile(archive):
        return False, "no such archive: %s" % archive
    if not os.path.isfile(sig):
        return False, "no signature beside %s (expected %s)" % (archive, sig)

    import tempfile
    home = tempfile.mkdtemp(prefix="axiom-gpg-")
    env = dict(os.environ, GNUPGHOME=home)
    try:
        if keyring:
            if not os.path.isfile(keyring):
                return False, "no such public key: %s" % keyring
            p = _gpg(["--import", keyring], env=env)
            if p.returncode != 0:
                return False, "could not import %s: %s" % (
                    keyring, (p.stderr or p.stdout).strip())
        p = _gpg(["--verify", sig, archive], env=env)
        out = (p.stderr or "") + (p.stdout or "")
        if p.returncode != 0:
            return False, out.strip()
        # "Good signature" alone is not enough: gpg prints it for a key it
        # cannot attribute. The fingerprint it actually used is what a reader
        # needs to compare against the one we published.
        fp = ""
        for line in out.splitlines():
            if "using" in line and "key" in line:
                fp = line.rsplit(None, 1)[-1]
        return True, "good signature, key %s" % (fp or "unreported")
    finally:
        import shutil
        shutil.rmtree(home, ignore_errors=True)


def export_key(fpr, out):
    p = _gpg(["--armor", "--export", fpr])
    if p.returncode != 0 or not p.stdout.strip():
        raise SystemExit("could not export %s: %s"
                         % (fpr, (p.stderr or p.stdout).strip()))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(p.stdout)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build, sign and verify a release.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--label", default=time.strftime("%Y-%m-%d"))

    s = sub.add_parser("sign")
    s.add_argument("--archive", required=True)
    s.add_argument("--key")

    v = sub.add_parser("verify")
    v.add_argument("--archive", required=True)
    v.add_argument("--keyring", help="public key file to verify against")
    v.add_argument("--signature")

    e = sub.add_parser("export-key")
    e.add_argument("--key", required=True)
    e.add_argument("--out", required=True)

    a = ap.parse_args(argv)

    if a.cmd == "build":
        archive, manifest, n = build(a.out, a.label)
        print("built %s (%d files, sha256 %s)"
              % (archive, n, _sha256(archive)[:16]))
        print("manifest %s" % manifest)
        return 0

    if a.cmd == "sign":
        sig = sign(a.archive, a.key)
        print("signed -> %s" % sig)
        return 0

    if a.cmd == "export-key":
        print("wrote %s" % export_key(a.key, a.out))
        return 0

    ok, detail = verify(a.archive, a.keyring, a.signature)
    print(("ok — " if ok else "FAILED — ") + detail)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
