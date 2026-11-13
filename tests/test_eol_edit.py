#!/usr/bin/env python3
"""Tests for tools/eol_edit.py.

The whole reason this tool exists is that a text round-trip rewrote endings and
turned small edits into enormous diffs. So every test here asserts on the BYTES
of the result, not on what a text read would report -- a text read normalises the
very thing under test and would pass whether or not the file was damaged.
"""
import os
import subprocess
import sys
import tempfile

TOOL = os.path.join(os.path.dirname(__file__), "..", "tools", "eol_edit.py")


def run(*args):
    proc = subprocess.run(
        [sys.executable, "-I", TOOL, *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


class Sandbox:
    """A temp dir with helper writers, so each test states its own bytes."""

    def __init__(self):
        self.dir = tempfile.mkdtemp()

    def path(self, name):
        return os.path.join(self.dir, name)

    def write(self, name, data: bytes):
        p = self.path(name)
        with open(p, "wb") as fh:
            fh.write(data)
        return p

    def read(self, name) -> bytes:
        with open(self.path(name), "rb") as fh:
            return fh.read()


def test_crlf_file_keeps_crlf():
    """The defect this tool exists to prevent: an LF-only rewrite of a CRLF file."""
    s = Sandbox()
    target = s.write("d.md", b"alpha\r\nBRAVO\r\ncharlie\r\n")
    old = s.write("old.txt", b"BRAVO\n")
    new = s.write("new.txt", b"delta\n")
    code, _, err = run(target, old, new)
    assert code == 0, err
    got = s.read("d.md")
    assert got == b"alpha\r\ndelta\r\ncharlie\r\n", got
    assert got.count(b"\r\n") == 3, got
    assert got.count(b"\n") == 3, got


def test_lf_file_keeps_lf():
    s = Sandbox()
    target = s.write("d.md", b"alpha\nBRAVO\ncharlie\n")
    old = s.write("old.txt", b"BRAVO\n")
    new = s.write("new.txt", b"delta\n")
    code, _, err = run(target, old, new)
    assert code == 0, err
    got = s.read("d.md")
    assert got == b"alpha\ndelta\ncharlie\n", got
    assert b"\r\n" not in got, got


def test_multiline_replacement_uses_file_ending():
    """A caller writes a plain two-line replacement; a CRLF file needs CRLF twice."""
    s = Sandbox()
    target = s.write("d.md", b"one\r\ntwo\r\nthree\r\n")
    old = s.write("old.txt", b"two\n")
    new = s.write("new.txt", b"two-a\ntwo-b\n")
    code, _, err = run(target, old, new)
    assert code == 0, err
    assert s.read("d.md") == b"one\r\ntwo-a\r\ntwo-b\r\nthree\r\n"


def test_no_match_refuses_and_writes_nothing():
    s = Sandbox()
    target = s.write("d.md", b"alpha\nbeta\n")
    before = s.read("d.md")
    old = s.write("old.txt", b"GAMMA\n")
    new = s.write("new.txt", b"delta\n")
    code, _, err = run(target, old, new)
    assert code == 1, code
    assert "no match" in err
    assert s.read("d.md") == before, "file must be untouched on a non-match"


def test_duplicate_match_refuses_and_writes_nothing():
    """An ambiguous edit is refused rather than silently applied to the first hit."""
    s = Sandbox()
    target = s.write("d.md", b"dup\ndup\n")
    before = s.read("d.md")
    old = s.write("old.txt", b"dup\n")
    new = s.write("new.txt", b"other\n")
    code, _, err = run(target, old, new)
    assert code == 2, code
    assert "ambiguous" in err
    assert s.read("d.md") == before


def test_show_ending_reports_counts():
    s = Sandbox()
    target = s.write("mixed.md", b"a\r\nb\r\nc\nd\n")
    code, out, err = run(target, "--show-ending")
    assert code == 0, err
    assert "CRLF=2" in out and "LF_ONLY=2" in out, out


def test_edit_hashing_a_docket_sized_file_is_single_line_diff():
    """End-to-end: a 200-line CRLF file stays byte-identical apart from the edit."""
    s = Sandbox()
    body = b"".join(b"line %03d\r\n" % i for i in range(200))
    target = s.write("big.md", body)
    old = s.write("old.txt", b"line 100\n")
    new = s.write("new.txt", b"line 100, edited\n")
    code, _, err = run(target, old, new)
    assert code == 0, err
    got = s.read("big.md")
    expected = body.replace(b"line 100\r\n", b"line 100, edited\r\n", 1)
    assert got == expected
    assert got.count(b"\r\n") == 200, got.count(b"\r\n")


class _report:
    def __init__(self):
        self.passed = 0
        self.failed = 0


def main():
    r = _report()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except AssertionError as exc:
                r.failed += 1
                print(f"FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                r.failed += 1
                print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            else:
                r.passed += 1
                print(f"PASS  {name}")
    print(f"\n{r.passed} passed, {r.failed} failed")
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
