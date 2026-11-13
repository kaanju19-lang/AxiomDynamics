# Frontend build — measured palette, vector sprite, and two defects found by measuring

**Chat-10, 2026-11-13. Commit `44a148f`. Suite 377 → 390.**
Files: `frontend/index.html`, `frontend/style.css`, `frontend/app.js`,
`frontend/icons.js` (new), `tests/test_frontend.py` (new).

---

## What was asked, and one correction to the premise

The owner asked for "a Professional Grade Enterprise Dashboard … with high vector
assets as seen in RailSentinel Prototype."

**There is no RailSentinel prototype in this repository.** The only occurrence
anywhere is inside `project-logs/transcripts/raw/2026-11-10-chat-3-snapshot.jsonl`,
in the text of commit `3b25d86` from an earlier project on 2026-11-08:

> "Enterprise visual overhaul: dispatch-center aesthetic with technical
> typography, minimal border-radius, improved KPI strip hierarchy, and refined
> warrant card design"

That commit is not in this repo's history. So the direction was taken from the
description rather than the artifact, and the read-back to the owner said so at
the time. If a RailSentinel visual reference exists somewhere, it was never in
this folder.

The two scope questions were put to the owner and answered: a **visible demo
band**, and **visual overhaul only** (no API or data-path change).

---

## Defect 1 — the palette failed WCAG AA everywhere it carried text

Found by computing relative luminance rather than by looking.

| Token | Colour | On white | AA needs 4.5:1 |
|---|---|---|---|
| accent (was) | `#0ea5e9` | **2.77:1** | FAIL |
| warning (was) | `#f59e0b` | **2.15:1** | FAIL |
| success (was) | `#10b981` | **2.54:1** | FAIL |
| error (was) | `#ef4444` | **3.76:1** | FAIL |
| muted (was) | `#64748b` | 4.76:1 | pass, barely |

These were used as text colours on badges, KPI values and the sign-in bar. Every
token is now chosen by computed contrast and the ratio is written beside it in
the stylesheet. `tests/test_frontend.py::test_tokens_are_measured_and_pass_aa`
re-computes each documented ratio and fails if the comment and the colour
disagree.

**A follow-on mistake worth recording:** the first pass wrote five ratios into
comments from mental arithmetic and four were wrong (e.g. `--ink-muted` recorded
5.61:1, measures 5.68:1). All corrected against the computed value. A comment
that misstates its own number is worse than no comment, which is why the test
asserts it rather than trusting the prose.

## Defect 2 — the chart palette was a dark theme on a light canvas

`drawLineChart` still carried the colours it was authored with when the canvas
was dark. On the light `#f4f6f9` canvas:

| Element | Was | Contrast on canvas |
|---|---|---|
| series line 1 | `#4fd6e0` | **1.61:1** |
| series line 2 | `#4fe0a0` | **1.55:1** |
| series line 3 | `#e0a94f` | **1.95:1** |
| axis text | `#7f93a8` | **2.92:1** |
| legend text | `#dbe6f0` | **1.17:1** |

The plots were very nearly invisible. This had been true since the canvas went
light and nothing caught it, because the numbers it draws were still correct and
no test reads pixels. Now every plotted colour clears 3:1 (AA for graphics) and
`test_chart_palette_is_legible_on_the_canvas` asserts it.

---

## What was built

**`frontend/icons.js`** — a 13-symbol sprite on one 24×24 grid with one stroke
weight, drawn in `currentColor` so an icon inherits its state colour rather than
baking a hex into a shape. Replaces four ad-hoc builders that each created a
throwaway `div`, parsed an HTML string into it and read back `firstElementChild`
— once per icon, once per table row. `<symbol>` parses once; `<use>` clones.

**Severity is no longer colour alone.** Each badge group carries a glyph — ● for
normal, ▲ for watch/review, ■ for critical/urgent — so state survives greyscale,
colour-blind viewing and a monochrome print. This is WCAG 1.4.1.

**The fleet table became keyboard-operable.** Rows open the detail panel on
click and had no tab stop, no role and no key handler: unusable without a mouse.
They now carry `tabindex="0"`, `role="button"`, an `aria-label`, and Enter/Space
handling with `preventDefault()` so Space does not also scroll the page.

**The demonstration band** is the first element in `<body>`, above the header and
not dismissible. Every number on the dashboard is computed from physics
equations over synthetic traces; a dashboard that looks authoritative without
saying so is the exact drift D00 Part VI exists to prevent. A test asserts the
band is above the header so a later refactor cannot quietly move it.

Also: `h1` lost its gradient-filled logotype (the most templated-looking element
a dashboard can carry, and it drops the wordmark below AA); near-square corners
and hairline rules replace drop shadows; tabular figures on every number that can
change; `prefers-reduced-motion` and `forced-colors` rules added.

---

## The test suite, and how it was attacked

13 checks of what a screenshot cannot prove: sprite well-formedness, icon
coverage in both directions, palette agreement between `icons.js` and
`style.css`, every documented contrast ratio, chart legibility, badge glyph
distinctness, keyboard reachability, script load order, and that the demo band
is above the header.

**Mutation-tested. Two of six first-round mutants survived, and both were real
defects in the tests, not in the code:**

1. **One mutation never applied.** A `python3` in-place replace used an LF needle
   against a CRLF file, so the string was absent, nothing changed, and the "pass"
   proved nothing. Caught by asserting the mutation had landed before believing
   the result. This is the same CRLF trap the repo has hit since chat-3, and it
   is why `tools/eol_edit.py` exists.

2. **The badge test asserted a selector existed, not that a glyph rendered.**
   Deleting `.badge.critical::before { content: "\25A0" }` left the selector
   behind and the test passed. Rewritten to read the rendered `content` out of
   each severity group and to require three *distinct* glyphs, so a copy-paste
   that gives every tier the same dot is caught too.

After the fixes all mutants die: palette drift, undefined icon, band moved below
the header, glyph deleted, glyphs made identical, a falsified contrast comment.

**What this suite cannot say:** whether the dashboard looks good. There is no
browser in the sandbox and the preview panel did not open, so nothing was
rendered and viewed. That was stated to the owner rather than papered over.

---

## The `eol_edit.py` tool

`tools/eol_edit.py` + 7 tests. Byte-level find/replace that preserves whatever
line endings the target already uses, with the replacement text's newlines
translated to match. Refuses an ambiguous edit (exit 2) and a non-match (exit 1)
rather than guessing, and writes nothing in either case. Built because this repo
has lost an hour to a line-ending rewrite three separate times.

Mutation-tested: dropping the newline translation, and swallowing the no-match
case, each turn a distinct test red.

**It was then not used for part of the frontend work, and that was a mistake.** A
`python3` heredoc rewrite stripped the CRLF endings from `app.js`, `style.css` and
`index.html` mid-session. Caught before commit by comparing byte counts against
the `HEAD:` blobs, and normalised back. The tool exists so this does not need
remembering; the reminder is that reaching for a heredoc is the reflex to
suppress.
