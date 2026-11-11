#!/usr/bin/env python3
"""Verify every docket citation made by the D07 §14.5 counsel brief and the
Phase 0 formation checklist against the actual docket files.

Run:  python3 -I assets/legal-architecture/check-legal-citations.py

Why this exists: the project's most repeated defect is a claim written from
memory and checked afterwards. Two documents were just written making several
dozen factual assertions about what other docket files say. This asserts them
against the files rather than against recollection.

It checks two classes of thing:
  1. LITERALS  - a figure one document attributes to another actually appears there.
  2. ABSENCES  - a claim that a file does NOT contain something is actually true.

A check that cannot find its anchor file is a FAILURE, not a skip: a citation
into a renamed document is a broken citation.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCKET = os.path.normpath(os.path.join(HERE, "..", "..",
                                       "client-assets", "MASTER-BRIEF-DOCKET"))
ASSETS = HERE  # Q6 lives beside this script, not in the docket

FAILS = []
CHECKS = 0


def read(name, folder=None):
    """Read a file by prefix (e.g. 'D07'). Fails loudly if absent.

    Q6 is internal analysis and lives in assets/legal-architecture, not the
    docket — the first run of this checker asserted otherwise and caught it.
    """
    folder = folder or DOCKET
    matches = [f for f in sorted(os.listdir(folder)) if f.startswith(name)]
    if not matches:
        raise FileNotFoundError("no docket file starts with %r" % name)
    if len(matches) > 1:
        raise RuntimeError("ambiguous prefix %r -> %r" % (name, matches))
    with open(os.path.join(folder, matches[0]), encoding="utf-8") as fh:
        return fh.read()


def check(label, condition, detail=""):
    global CHECKS
    CHECKS += 1
    if condition:
        print("PASS  %s" % label)
    else:
        print("FAIL  %s%s" % (label, ("  -> " + detail) if detail else ""))
        FAILS.append(label)


def has(label, text, needle, where):
    check(label, needle in text, "%r not found in %s" % (needle, where))


def hasnt(label, text, needle, where):
    check(label, needle not in text, "%r SHOULD be absent from %s" % (needle, where))


def main():
    d02 = read("D02")
    d03 = read("D03")
    d07 = read("D07")
    d08 = read("D08")
    q6 = read("Q6", ASSETS)
    d00 = read("D00")

    print("=" * 78)
    print("D07 §14.5 counsel brief — the figures it attributes")
    print("=" * 78)

    # --- The pilot fee, and its five components (brief §3, §4, §6, Track B) ---
    has("D02 states the $370,000 pilot fee", d02, "$370,000", "D02")
    for amount, what in [("$180,000", "pilot licence"), ("$65,000", "commissioning"),
                         ("$40,000", "training"), ("$35,000", "validation"),
                         ("$50,000", "support")]:
        has("D02 line item %s %s" % (amount, what), d02, amount, "D02")

    has("D08 states $370,000 pilot year", d08, "$370,000", "D08")
    has("D08 states $1,050,000/yr at 2,000 axles", d08, "$1,050,000", "D08")
    has("D08 states $300,000/yr at 500 axles", d08, "$300,000", "D08")
    has("D08 states the $1,180,000 three-year single-yard total", d08, "$1,180,000", "D08")

    # --- The liability cap (brief §2(c)) ---
    has("D07 §8.1 caps at twelve months' fees", d07, "twelve months", "D07")
    has("D07 names the $370,000 pilot cap", d07, "$370,000", "D07")
    has("D07 names the $1,050,000 production cap", d07, "$1,050,000", "D07")

    # --- D03 delegation (brief §2(b), §8 step 5) ---
    has("D03 delegates venue to D07 §14.5", d03, "D07 §14.5", "D03")
    has("D03 says it holds no second venue blank", d03,
        "does not hold a second, independent venue blank", "D03")
    has("D03 describes drift across instruments", d03,
        "they drift", "D03")

    # --- D07 §14 structure the brief relies on ---
    has("D07 §14.5 is labelled an open item", d07,
        "an open item requiring counsel decision", "D07")
    has("D07 §14.5(b) requires a signed addendum", d07, "signed addendum", "D07")
    has("D07 §14.5(d) fallback is the stated-fallback mechanic", d07,
        "fallback, not a preference", "D07")
    has("D07 §14.6 each party bears own costs", d07,
        "Each party bears its own costs", "D07")
    has("D07 §14.2 carries the provider bracket", d07,
        "[the mediation rules of the chosen provider]", "D07")
    has("D07 §14.2 requires 30-day mediation", d07, "thirty (30) days", "D07")

    # --- Phase 0 / Q6 figures ---
    has("Q6 states the $300 Form 205 fee", q6, "$300", "Q6")
    has("Q6 states the $2,650,000 franchise threshold", q6, "$2,650,000", "Q6")
    has("Q6 states the 15 May PIR deadline", q6, "15 May", "Q6")
    has("Q6 states the $40 name reservation", q6, "$40", "Q6")
    has("Q6 recommends a Texas LLC", q6, "Texas limited liability company", "Q6")
    has("Q6 warns about personal guarantees", q6, "personal guarantee", "Q6")
    has("Q6 hands the venue question to D07 §14.5", q6,
        "which is D07 §14.5", "Q6")

    # --- Insurance limits: D03 §9 and D07 §10 must agree (Track B5) ---
    has("D03 states CGL $1,000,000 / $2,000,000", d03,
        "$1,000,000 per occurrence / $2,000,000 aggregate", "D03")
    has("D03 states E&O $2,000,000 per claim", d03, "$2,000,000 per claim", "D03")
    has("D03 states Cyber $1,000,000", d03, "$1,000,000 per claim", "D03")
    has("D03 states the $5,000,000 step-up", d03, "$5,000,000", "D03")
    has("D03 warns $5M is not purchasable pre-revenue", d03,
        "not purchasable by a pre-revenue company", "D03")
    has("D07 states the $5,000,000 step-up", d07, "$5,000,000", "D07")
    has("D07 states the step-up trigger at $1,000,000 revenue", d07, "$1,000,000", "D07")

    # --- D00: USPTO is a named Phase 0 item (Track D) ---
    has("D00 names USPTO among Phase 0 items", d00, "USPTO", "D00")
    has("D00 names the Phase 0 pre-signature set", d00, "Phase 0 pre-signature", "D00")

    print()
    print("=" * 78)
    print("Absences the documents assert — these are the claims that rot")
    print("=" * 78)

    # The brief §9 says the construction-contract statute does NOT apply.
    # It should not appear in any docket document as if it were operative.
    hasnt("no docket document cites Chapter 272 as operative", d02 + d03 + d07,
          "272.001", "D02/D03/D07")

    # The brief asserts the withdrawn 2.0x/4.1x pair is gone (chat-4 closed it).
    # Re-asserted here because the brief quotes 1.77x context indirectly.
    hasnt("withdrawn 2.0x anchor absent from D08 as live claim", d08, "2.0x", "D08")
    hasnt("withdrawn 4.1x anchor absent from D08 as live claim", d08, "4.1x", "D08")

    # D02 §16 should be a summary, not a second venue term (brief §2(b) relies
    # on D07 being the single home for the decision).
    hasnt("D02 §16 carries no competing venue term", d02,
          "exclusive jurisdiction", "D02")

    # The 500-axle production fee is $550,000 and the brief does not call it
    # over $1M; assert the brief's threshold reasoning has a sub-$1M case.
    check("a production year can fall below the $1M threshold",
          "$550,000" in d08,
          "D08 should state $550,000 at 1,000 axles")

    print()
    print("=" * 78)
    if FAILS:
        print("%d of %d checks FAILED:" % (len(FAILS), CHECKS))
        for f in FAILS:
            print("   - %s" % f)
        return 1
    print("All %d checks passed." % CHECKS)
    print("Every figure the two documents attribute to the docket is present,")
    print("and every absence they assert is actually absent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
