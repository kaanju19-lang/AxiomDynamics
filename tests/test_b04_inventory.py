#!/usr/bin/env python3
"""B04's component inventory must match the code it claims to describe.

B04 opens by stating that every figure in it was checked against the code. The
inventory table then went four chats without changing while seven backend
modules were added, so it described 2,695 lines of a codebase that had grown to
8,200 -- and the seven it omitted were the cryptographic and authentication
modules a security reviewer spends their time on.

Correcting the table once does not fix that, because the same drift resumes the
moment the next module is written. So the table is now tested: every file it
names must exist with the line count it quotes, nothing in backend/ or
frontend/ may be missing from it, and the quoted total must equal the sum.

Deliberately NOT tested: that the numbers are "right" in some absolute sense.
The test's job is to make the document and the repository disagree loudly, and
it derives both sides from disk rather than from a list written here.
"""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DOCKET = os.path.join(ROOT, "client-assets", "MASTER-BRIEF-DOCKET")
B04 = os.path.join(DOCKET, "B04-TECHNOLOGY-STACK-DISCLOSURE.md")

# A table row naming a source file and its line count:
#   | Dashboard logic | `frontend/app.js` | 595 | Vanilla JavaScript |
ROW = re.compile(r"^\|\s*[^|]+\|\s*`([a-z]+/[A-Za-z0-9_]+\.(?:py|js|css|html))`\s*\|\s*([0-9,]+)\s*\|", re.M)


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def counted():
    """{relative path: physical line count} for every file the table may name."""
    out = {}
    for sub in ("backend", "frontend"):
        d = os.path.join(ROOT, sub)
        for name in sorted(os.listdir(d)):
            if not name.endswith((".py", ".js", ".css", ".html")):
                continue
            path = os.path.join(d, name)
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as fh:
                out[f"{sub}/{name}"] = fh.read().count(b"\n")
    return out


def table_rows():
    return {m.group(1): int(m.group(2).replace(",", ""))
            for m in ROW.finditer(read(B04))}


def test_every_named_file_exists_with_the_stated_line_count():
    rows, actual = table_rows(), counted()
    assert rows, "the inventory table parsed as empty -- the format changed"
    wrong = []
    for path, quoted in sorted(rows.items()):
        if path not in actual:
            wrong.append(f"{path}: named in B04, not on disk")
        elif actual[path] != quoted:
            wrong.append(f"{path}: B04 says {quoted}, disk has {actual[path]}")
    assert not wrong, "B04 inventory is stale:\n  " + "\n  ".join(wrong)


def test_no_module_is_missing_from_the_inventory():
    """The defect that prompted this test: modules added, table not updated."""
    rows, actual = table_rows(), counted()
    missing = sorted(set(actual) - set(rows))
    # __init__.py is empty and carries no component; every other file is named.
    missing = [m for m in missing if not m.endswith("__init__.py")]
    assert not missing, "B04 omits code that exists: " + ", ".join(missing)


def test_the_quoted_total_equals_the_sum_of_the_rows():
    rows = table_rows()
    text = read(B04)
    m = re.search(r"^\|\s*\*\*Total\*\*\s*\|\s*\|\s*\*\*([0-9,]+)\*\*\s*\|", text, re.M)
    assert m, "the Total row is missing or changed format"
    quoted = int(m.group(1).replace(",", ""))
    assert quoted == sum(rows.values()), (
        f"total says {quoted}, rows sum to {sum(rows.values())}")


def test_the_supply_chain_section_does_not_claim_a_tool_is_absent():
    """A tool that exists is 'built, not applied' -- never 'not produced'.

    This is the second half of the same defect. B04 said 'Not produced' and
    'Not currently signed' while tools/sbom.py and tools/sign_release.py both
    existed and were tested.
    """
    text = read(B04)
    forbiddens = ["**Not produced.**", "Not currently signed",
                  "Not currently performed"]
    for phrase in forbiddens:
        assert phrase not in text, (
            f"B04 still says {phrase!r}, but the tool exists -- state it as "
            "'built, not applied'")


def test_every_supply_chain_row_names_its_three_state():
    """Each of the five controls must say built/not built/applied explicitly."""
    text = read(B04)
    section = text.split("## 7. Build and supply chain")[1].split("## 8.")[0]
    rows = [ln for ln in section.splitlines() if ln.startswith("| ") and "---" not in ln]
    # header + five controls
    assert len(rows) == 6, f"expected 6 table lines in section 7, found {len(rows)}"
    for ln in rows[1:]:
        assert ("**Tool built, not applied.**" in ln
                or "**Applied.**" in ln
                or "**Not built.**" in ln), f"row states no three-state status: {ln[:90]}"


def main():
    """Run standalone AND be discovered by run_tests.py.

    Without this, `python3 tests/test_b04_inventory.py` exits 0 having run
    nothing -- the silent-test-file shape this project has hit before, where a
    module counts toward the suite total while testing nothing.
    """
    r = type("R", (), {"passed": 0, "failed": 0})()
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
