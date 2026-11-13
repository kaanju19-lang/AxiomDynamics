#!/usr/bin/env python3
"""Guards against the docket claiming a built thing is absent, or vice versa.

Two defects of the same shape were found in chat-11, in two different documents:

  * B04's inventory omitted seven backend modules and called the SBOM and
    release-signing tools "not produced" while both existed and were tested.
  * B02 §9 said "The ingest path (§2) is not built at all" -- seventeen chats and
    several thousand lines of code after the ingest path was built, and in
    contradiction of B02's own §2, which said the chain ran as drawn.

Both are the failure the project already names: when a gap closes, the documents
that described it do not close with it. The rule that follows is *grep for every
phrasing*, and a human doing that by hand will miss one. These tests are the
mechanical half of it: for each capability the code demonstrably has, no docket
document may assert that it is absent.

Deliberately NOT tested: that the documents are accurate in other respects. These
checks only catch the "says absent, is present" direction, which is the one that
silently understates the product to a customer.

Chat-12 added the opposite direction, because chat-11's lesson was that staleness
runs both ways: D10 claimed a GPG key "is issued and published" while D09 and B04
said none exists, and no absence-grep could ever have found it. The second test
below is that shape -- a document promising a *capability* the software does not
have. It is a much smaller net than the first (a phrase list, not a semantic
search), and it is a net for the two specific claims this project has already
made wrongly, not a general guarantee.
"""
import glob
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DOCKET = os.path.join(ROOT, "client-assets", "MASTER-BRIEF-DOCKET")


def docket_text():
    """(path, text) for every Markdown document in the docket."""
    for path in sorted(glob.glob(os.path.join(DOCKET, "*.md"))):
        with open(path, "rb") as fh:
            yield path, fh.read().decode("utf-8", "replace")


def offenders(needles, also_file_must_exist=None):
    """Documents containing any of these phrases, with the matched phrase."""
    hits = []
    for path, text in docket_text():
        for needle in needles:
            if needle in text:
                hits.append(f"{os.path.basename(path)}: {needle!r}")
    return hits


# Each entry: (label, [phrases that assert absence], the file whose existence
# proves the capability is present). A phrase may legitimately appear where it
# is immediately retracted -- so any document containing "no longer" within the
# same line is skipped, which is how a correction is written.
CAPABILITIES = [
    ("sensor ingest",
     ["ingest path (§2) is not built at all",
      "The ingest path is not built",
      "the front door does not yet exist"],
     "backend/ingest.py"),
    ("SBOM generator",
     ["**Not produced.**", "No SBOM artefact is produced"],
     "tools/sbom.py"),
    ("release signing",
     ["Not currently signed.", "No release has been signed"],
     "tools/sign_release.py"),
    ("dependency pinning",
     ["Not currently performed. Production should use"],
     "tools/pin_requirements.py"),
    ("signed key directory",
     ["no signed key directory", "The signed key directory is not built"],
     "backend/key_directory.py"),
    ("append-only ledger",
     ["the ledger is not append-only", "the ledger is not built"],
     "backend/store.py"),
]


def _assert_capability_present(path):
    assert os.path.isfile(os.path.join(ROOT, path)), (
        f"{path} is missing -- this check is guarding the wrong thing")


def test_no_document_claims_a_built_capability_is_absent():
    problems = []
    for label, needles, proving_file in CAPABILITIES:
        _assert_capability_present(proving_file)
        for path, text in docket_text():
            for line in text.splitlines():
                if "no longer" in line.lower():
                    continue          # a retraction, which is the fix
                for needle in needles:
                    if needle in line:
                        problems.append(
                            f"{os.path.basename(path)} says the {label} "
                            f"is absent ({needle!r}), but {proving_file} exists")
    assert not problems, "stale absence claims:\n  " + "\n  ".join(problems)


def test_b02s_own_sections_do_not_contradict_each_other_on_ingest():
    """The specific contradiction: §2 said built, §9 said not built at all."""
    path = os.path.join(DOCKET, "B02-FLOW-MAP.md")
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    says_built = "The chain now runs as drawn" in text
    # A retraction quotes the old claim AND calls it corrected; that is the fix,
    # not the defect. Only an unretracted assertion counts.
    says_absent = any(
        "is not built at all" in ln and "stopped" not in ln and "corrected" not in ln
        for ln in text.splitlines())
    assert not (says_built and says_absent), (
        "B02 §2 says the chain runs as drawn while §9 says it is not built at all")


# The mirror image: claims of PRESENCE that the code does not support. Each
# entry is (label, phrases asserting the capability exists, a predicate name that
# must be True for the claim to be honest). These were all false at some point in
# this project's history, so each is pinned by the exact wording that was wrong.
def _no_admin_purge_route():
    """True when the Platform exposes no way to delete ledger records."""
    main_py = os.path.join(ROOT, "backend", "main.py")
    with open(main_py, "rb") as fh:
        src = fh.read().decode("utf-8", "replace")
    # A DELETE handler exists for sign-out only. Any purge route would need a
    # handler that calls a delete on the dispositions table.
    return "route_purge" not in src and "purge_ledger" not in src


def _no_issued_gpg_key():
    """True when no release signing key is issued or under custody."""
    # The tool exists; the key does not. A key file under the repo would falsify
    # this, so look for the one path the custody procedure names.
    return not glob.glob(os.path.join(ROOT, "**", "release-signing*.key"),
                         recursive=True)


PRESENCE_CLAIMS = [
    ("admin purge interface",
     ["purging records from the platform (via an admin interface or sql)",
      "via an admin interface or SQL"],
     _no_admin_purge_route),
    ("issued GPG release key",
     ["The key is issued and published by Supplier"],
     _no_issued_gpg_key),
]


def test_no_document_claims_a_capability_that_does_not_exist():
    problems = []
    for label, needles, predicate in PRESENCE_CLAIMS:
        if not predicate():
            continue          # the capability now exists; the claim is fair
        for path, text in docket_text():
            for line in text.splitlines():
                # A retraction quotes the phrase it retracts. Any line that is
                # itself doing the retracting is skipped -- "no longer",
                # "corrected", or a quoted phrase introduced as a former claim
                # (the wording this project uses: was / previously / does not).
                low = line.lower()
                if ("no longer" in low or "corrected" in low
                        or "previous" in low or "does not" in low
                        or "as a routine means of" in low):
                    continue
                for needle in needles:
                    if needle.lower() in line.lower():
                        problems.append(
                            f"{os.path.basename(path)} claims a {label} exists "
                            f"({needle!r}), but the code does not provide one")
    assert not problems, "false presence claims:\n  " + "\n  ".join(problems)


def test_every_capability_guard_names_a_file_that_is_still_where_it_was():
    """If a module moves, the guard would pass vacuously. Fail loudly instead."""
    for label, _needles, proving_file in CAPABILITIES:
        assert os.path.isfile(os.path.join(ROOT, proving_file)), (
            f"guard for {label} points at {proving_file}, which does not exist")


def main():
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
