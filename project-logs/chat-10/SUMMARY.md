# Chat-10 — Summary

**2026-11-13. Suite 370 → 390. Two commits. Eight unpushed at close.**

The owner opened by restating the four standing rules (125K cap, low→high
ladder, caching discipline, Master % Tracker) and adding one: a professional
enterprise dashboard with vector assets.

---

## One correction to the request

**"As seen in RailSentinel Prototype" pointed at something that is not in this
repository.** The only occurrence of the name anywhere is inside chat-3's raw
transcript, quoting a commit message from a different project on 2026-11-08. The
direction was therefore taken from that description — dispatch-center aesthetic,
technical typography, minimal border-radius, refined card hierarchy — and the
owner was told plainly that the artifact itself could not be opened.

## Item 1 — four documents still said entry needed no attestation

Chat-9 made attestation a condition of a disposition row existing. Four documents
still described the old state: D00 Part VI's certification-registry row, D00's
own export row (which carried a garbled *"but a attestation is now required at
entry"* where the sentence it replaced had been), D09 §4.4's Authentication row
and its status cell, and F08's "why this form exists" block.

**Why chat-9's sweep missed them is the transferable part.** Its close-gate guard
greps `"entry is not yet gated"` — one phrasing. All four are phrased *"but not
an attestation"*. The gate worked exactly as written and could not see them. A
second guard now covers that family, proved to fire by injecting the claim into a
temp copy.

Also corrected: D00 Part V's "four controls remain unbuilt" (the SBOM, hash-pinning
and signing controls are built and unapplied, not unbuilt), and CURRENT-STATE's
build-history page count, which claimed 39 and measures 46.

`close-gate.sh`'s header comment still named a chat-7 session path; removed.

## Item 2 — the enterprise frontend pass

Two real defects, both found by measuring rather than looking:

**The palette failed WCAG AA wherever it carried text.** Accent 2.77:1, warning
2.15:1, success 2.54:1, error 3.76:1, against a 4.5:1 requirement. Every token is
now chosen by computed relative luminance with the ratio written beside it, and a
test recomputes each documented ratio and fails on disagreement.

**The chart palette was a dark theme left on a light canvas.** Series lines
measured 1.55–1.95:1 — effectively invisible. True since the canvas went light,
and missed because the numbers it drew were still correct and no test reads
pixels.

Built: a 13-symbol SVG sprite on one grid in `currentColor`, replacing four
per-cell HTML-string parsers; distinct glyphs per severity so state survives
greyscale; keyboard-reachable fleet rows (they were click-only); a non-dismissible
demonstration band above the header; reduced-motion and forced-colours rules.

## What the mutation testing found

Six mutants, two survivors, **both defects in the tests**:

- One mutation **never applied** — an LF needle against a CRLF file. The run
  proved nothing until I asserted the edit had landed.
- The badge test asserted a selector *existed*, not that a glyph *rendered*.
  Deleting the content passed.

Both fixed; all mutants now die.

## New tooling

`tools/eol_edit.py` + 7 tests — byte-level find/replace preserving each file's own
line endings, refusing ambiguous and non-matching edits. Built because the repo
has lost an hour to line-ending rewrites three times. **Then not used for part of
the frontend work, and CRLF was stripped from three files as a result.** Caught
before commit by comparing against the `HEAD:` blobs and normalised back.

## What remains unverified

**The dashboard has never been rendered.** No browser in the sandbox, and the
preview panel would not open. The 13 structural checks pass; they say nothing
about whether it looks good. Item 1 of chat-11's ladder is the owner opening it.

## Tracker

77.0 → 79.1. Only core software moved (+2.1), because the presentation layer was
the weakest of eight components and is now defensible — and because nothing
behind it reads a Railroad payload. Document corrections earn nothing under this
basis, and counting them would be how a tracker stops meaning anything.
