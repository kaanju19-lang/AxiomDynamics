"""
Tests for tools/issue_reviewer_key.py (D09 §8.4.2, the joiner step).

The failure this suite is written against is not "the script crashes". It is a
credential issue that *appears* to succeed and leaves the reviewer unable to
attest, or leaves two copies of a key where there should be one:

  * a key file written for a registration the registry refused — bytes on disk
    that no registry entry names, and that will be walked past by a later run;
  * an existing key file overwritten, destroying the only copy of a credential
    that an append-only registry cannot re-register once revoked.

Each is tested by driving the real CLI, not by re-implementing it.

Run: python3 -I tests/test_issue_reviewer_key.py
"""

import importlib.util
import os
import stat
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TOOL = os.path.join(ROOT, "tools", "issue_reviewer_key.py")
spec = importlib.util.spec_from_file_location("issue_reviewer_key", TOOL)
issue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(issue)

RESULTS = []


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


class _Tmp:
    def __enter__(self):
        self.d = tempfile.mkdtemp()
        self.db = os.path.join(self.d, "t.db")
        return self

    def path(self, name):
        return os.path.join(self.d, name)

    def __exit__(self, *a):
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)
        return False


@test
def test_it_writes_a_32_byte_key_mode_0600_and_registers_it():
    with _Tmp() as t:
        kf = t.path("hoffman.key")
        rc = issue.main(["--reviewer", "Hoffman", "--cert", "CERT-H-1",
                         "--key-file", kf, "--db", t.db])
        assert rc == 0, rc
        with open(kf, "rb") as fh:
            key = fh.read()
        assert len(key) == 32, len(key)
        mode = stat.S_IMODE(os.stat(kf).st_mode)
        assert mode == 0o600, oct(mode)

        from backend import attribution
        rows = attribution.registry(t.db)
        assert len(rows) == 1, rows
        assert rows[0]["reviewer"] == "Hoffman", rows[0]
        assert rows[0]["cert_id"] == "CERT-H-1", rows[0]
        assert rows[0]["key_id"] == attribution.key_id(key), rows[0]


@test
def test_it_refuses_to_overwrite_an_existing_key_file():
    # A key file is the only copy of a credential. Overwriting it would leave a
    # registry entry whose bytes are gone, and the registry is append-only.
    with _Tmp() as t:
        kf = t.path("hoffman.key")
        with open(kf, "wb") as fh:
            fh.write(b"x" * 32)
        rc = issue.main(["--reviewer", "Hoffman", "--cert", "CERT-H-1",
                         "--key-file", kf, "--db", t.db])
        assert rc == 2, "overwrite must be refused with rc 2, got %r" % (rc,)
        with open(kf, "rb") as fh:
            assert fh.read() == b"x" * 32, "the existing key file was modified"


@test
def test_a_refused_registration_leaves_no_key_file():
    # Register Okafor with a key, then try to register the *same* reviewer name
    # under a certificate that will be refused for a different reason: a
    # database that cannot be opened. The observable is the key file.
    with _Tmp() as t:
        kf = t.path("orphan.key")
        rc = issue.main(["--reviewer", "X", "--cert", "C",
                         "--key-file", kf,
                         "--db", os.path.join(t.d, "no", "such", "dir.db")])
        assert rc != 0, "a failed registration must not report success"
        assert not os.path.exists(kf), \
            "a key file was written for a registration that was refused"


@test
def test_two_reviewers_get_distinct_keys():
    with _Tmp() as t:
        a = t.path("a.key")
        b = t.path("b.key")
        assert issue.main(["--reviewer", "Hoffman", "--cert", "CERT-H-1",
                           "--key-file", a, "--db", t.db]) == 0
        assert issue.main(["--reviewer", "Okafor", "--cert", "CERT-O-1",
                           "--key-file", b, "--db", t.db]) == 0
        with open(a, "rb") as fh:
            ka = fh.read()
        with open(b, "rb") as fh:
            kb = fh.read()
        assert ka != kb, "two reviewers were issued the same key bytes"


if __name__ == "__main__":
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else " -> %s" % exc))
    print("\n%d passed, %d failed" % (passed, failed))
    sys.exit(1 if failed else 0)
