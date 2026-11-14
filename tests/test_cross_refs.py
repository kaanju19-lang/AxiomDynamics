"""Cross-references between docket documents name sections that exist.

Added chat-13. The two worst document defects this project has found -- D10's
inventory claim in chat-11 and D09's termination sentence in chat-12 -- were
one document contradicting another. Nothing tested that direction.

**Plain module-level ``test_*`` functions, not a ``unittest.TestCase``.**
``tests/run_tests.py`` collects ``dir(mod)`` for names starting with ``test_``;
a class-based file imports cleanly, contributes nothing, and the suite total
still looks healthy. That is the silent-test-file trap this project has hit
before.

The resolution tests exist because the first version of the tool was a guard
that could not fail: it compared section numbers by raw string prefix, so an
injected ``D07 §99.9`` resolved against a heading numbered ``9``.
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import check_cross_refs as xref  # noqa: E402

DOCKET = os.path.join(ROOT, "client-assets", "MASTER-BRIEF-DOCKET")


def test_exact_match_resolves():
    assert xref.resolves("4.2", {"4.1", "4.2"})


def test_parent_resolves_against_child():
    assert xref.resolves("4", {"4.1", "4.2"})


def test_child_resolves_against_parent():
    assert xref.resolves("4.5.1", {"4.5"})


def test_letter_suffix_is_the_same_section():
    assert xref.resolves("4.5", {"4.5a"})


def test_a_higher_second_segment_does_not_resolve():
    assert not xref.resolves("14.7", {"1", "14.1", "14.2"})


def test_string_prefix_does_not_count_as_a_parent():
    # "14.7" must not resolve against "1". This is the defect that made the
    # first version of the tool pass its own mutation.
    assert not xref.resolves("14.7", {"1"})


def test_non_numeric_headings_do_not_resolve():
    assert not xref.resolves("99.9", {"1", "4"})


def test_no_unresolved_cross_references_in_the_docket():
    before = os.getcwd()
    try:
        os.chdir(ROOT)
        assert xref.main(["check_cross_refs.py", DOCKET]) == 0
    finally:
        os.chdir(before)


def test_detects_an_injected_dangling_reference():
    """The guard's own mutation test. A copy of the docket gets a reference to
    a section that does not exist and the tool must go red."""
    tmp = tempfile.mkdtemp(prefix="xref-")
    try:
        copy = os.path.join(tmp, "docket")
        shutil.copytree(DOCKET, copy)
        victim = None
        for name in os.listdir(copy):
            if name.startswith("F13-") and name.endswith(".md"):
                victim = os.path.join(copy, name)
        assert victim is not None, "no F13-*.md to mutate"
        with open(victim, "a", encoding="utf-8") as fh:
            fh.write("\nSee D07 §99.9 and B01 §14.7.\n")
        assert xref.main(["check_cross_refs.py", copy]) == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
