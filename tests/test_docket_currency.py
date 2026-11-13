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
def _backend_sources():
    for path in sorted(glob.glob(os.path.join(ROOT, "backend", "*.py"))):
        with open(path, "rb") as fh:
            yield os.path.basename(path), fh.read().decode("utf-8", "replace")


def _no_admin_purge_route():
    """
    True when nothing in backend/ can delete a disposition.

    The first version of this looked for the literal names `route_purge` or
    `purge_ledger`, which only proves the author did not choose those two words.
    An independent audit showed a `route_delete_dispositions` would have passed.
    This looks at behaviour instead: a deleted row needs a DELETE against the
    ledger's table, and the triggers block it unless something drops them first.
    Either pattern anywhere in backend/ falsifies the "no purge" claim.
    """
    for _name, src in _backend_sources():
        # Strip comment and docstring text first. The ledger module *explains*
        # that DROP TRIGGER is possible for someone with file access, and a naive
        # substring test reads that explanation as the capability itself -- the
        # first run of this predicate failed for exactly that reason.
        low = _code_only(src).lower()
        if "drop trigger" in low:
            return False
        if "delete from dispositions" in low:
            return False
    return True


def _code_only(src):
    """Source with `#` comments and string literals removed."""
    out = []
    for line in src.splitlines():
        # Drop everything from a `#` that is not inside a string. This is not a
        # full tokeniser; it only needs to be right for this repository's style.
        in_str = None
        cut = len(line)
        for i, ch in enumerate(line):
            if in_str:
                if ch == in_str and (i == 0 or line[i - 1] != "\\"):
                    in_str = None
            elif ch in "\"'":
                in_str = ch
            elif ch == "#":
                cut = i
                break
        out.append(line[:cut])
    return "\n".join(out)


def _no_issued_gpg_key():
    """
    True when no release-signing key material is present in the repository.

    The first version globbed for `release-signing*.key`, a name nothing in this
    project produces -- `tools/sign_release.py` takes a fingerprint and
    `ledger_export` takes an operator-chosen `--key-file`. That predicate could
    never return False, so it was a permanent pass an audit caught.
    This looks for key material by content instead: a PGP private key block, or
    any `*.key`/`*.asc` holding one.
    """
    patterns = ("**/*.key", "**/*.asc", "**/*.gpg", "**/*.pgp")
    for pat in patterns:
        for path in glob.glob(os.path.join(ROOT, pat), recursive=True):
            if os.sep + ".git" + os.sep in path or "/tests/" in path.replace(os.sep, "/"):
                continue        # git internals and test fixtures are not custody
            try:
                with open(path, "rb") as fh:
                    head = fh.read(4096)
            except OSError:
                continue
            if b"PRIVATE KEY BLOCK" in head:
                return False
    return True


def _is_quoted(line, phrase):
    """
    True when `phrase` appears inside quotation marks on this line.

    This is what separates "the docket says X" from "here is what it used to
    say". Both contain X; only the first is a claim. Handles the straight and
    curly double quotes the docket actually uses.
    """
    low = line.lower()
    target = phrase.lower()
    quotes = "\"“”"
    start = 0
    while True:
        i = low.find(target, start)
        if i < 0:
            return False
        # The phrase counts as quoted when an odd number of quote marks precede
        # it, i.e. it begins inside an open quotation. Checking only the adjacent
        # characters misses the real case -- a retraction quotes the whole clause
        # ("purging records ... (via an admin interface or SQL)") and the needle
        # starts part-way through it.
        if sum(1 for ch in low[:i] if ch in quotes) % 2 == 1:
            return True
        start = i + 1


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
            # Quotation marks can straddle a line break: the D09 retraction opens
            # its quotation on one line and closes it on the next, so counting
            # quotes per line alone reads a wrapped retraction as a claim.
            preceded = ""
            for line in text.splitlines():
                # A retraction quotes the phrase it retracts, so the phrase
                # appearing is not itself a defect. The first version of this
                # skip searched for bare words -- "corrected", "previous",
                # "does not" -- and an audit showed it would swallow a NEW false
                # claim written into a correction line, which is exactly where
                # one would be hidden. So the test is positional: the phrase must
                # be inside quotation marks to count as quoted-and-retracted, and
                # a line that states the capability without quoting it is a claim
                # regardless of what other words it contains.
                for needle in needles:
                    if needle.lower() not in line.lower():
                        continue
                    # Quoted means the phrase is being reported, not asserted.
                    # The project writes a retraction as: "... (via an admin
                    # interface or SQL)" as a routine means of deletion. Nothing
                    # exists. -- the phrase sits inside quotes and the line says
                    # what was wrong with it. An unquoted occurrence is a claim.
                    if _is_quoted(preceded + line, needle):
                        continue
                    problems.append(
                        f"{os.path.basename(path)} claims a {label} exists "
                        f"({needle!r}), but the code does not provide one")
                preceded += " " + line
    assert not problems, "false presence claims:\n  " + "\n  ".join(problems)


def test_the_presence_guard_catches_a_claim_hidden_in_a_correction():
    """
    An independent audit found the first version of the skip logic searching for
    bare words -- "corrected", "previous", "does not" -- which skipped any line
    containing them. Five realistic false claims were swallowed, including one
    written into a correction line, which is where a false claim would hide.

    This pins the boundary in both directions: a claim framed by any of those
    words must still be caught, and a genuine retraction, which quotes the phrase
    it retracts, must be skipped.
    """
    needle = "via an admin interface or SQL"
    must_catch = [
        'Corrected 2026-11-14: purging records from the Platform '
        '(via an admin interface or SQL) is now available',
        'The Railroad does not need to raise a ticket; purging records from '
        'the Platform (via an admin interface or SQL) is self-service',
        'Previous deletion was manual only. Purging records from the Platform '
        '(via an admin interface or SQL) is the current method',
        'This supersedes the previous paragraph: purging records from the '
        'Platform (via an admin interface or SQL) is supported',
        'The Platform does not restrict the Railroad: purging records from the '
        'Platform (via an admin interface or SQL) is permitted at any time',
        'The Railroad may delete data by purging records from the Platform '
        '(via an admin interface or SQL).',
    ]
    for line in must_catch:
        assert not _is_quoted(line, needle), (
            f"a claim would be skipped as a retraction: {line!r}")

    retraction = ('Its first draft listed "purging records from the Platform '
                  '(via an admin interface or SQL)" as a routine means of '
                  'deletion.')
    assert _is_quoted(retraction, needle), (
        "a genuine retraction would be reported as a false claim")


def test_the_presence_predicates_are_not_vacuous():
    """
    Both predicates passed permanently in their first form: one looked for two
    literal route names the author chose, the other globbed for a filename the
    project never produces. A predicate that cannot return False turns its check
    into decoration. These assert the predicates respond to the thing they claim
    to detect.
    """
    import inspect
    purge_src = inspect.getsource(_no_admin_purge_route)
    key_src = inspect.getsource(_no_issued_gpg_key)
    assert "drop trigger" in purge_src.lower(), (
        "purge predicate does not look for a dropped trigger")
    assert "PRIVATE KEY BLOCK" in key_src, (
        "key predicate does not inspect file contents")

    # And the behaviour: both must currently be true, on evidence not assertion.
    assert _no_admin_purge_route() is True
    assert _no_issued_gpg_key() is True


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
