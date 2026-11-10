# Chat-4 — Summary

Status: **closed 2026-11-10.** Handoff for the next session is
`project-logs/chat-5/CARRY-FORWARD.md`.
Opened with the chat-3 carry-forward. Its first act was to verify the inherited
state against the repository rather than trust the handoff, per the standing rule.

## Verification of inherited state (start of chat-4)

The carry-forward named a remote ref of `bb99cdd` with work waiting on top of it.
Checked with git: the local ref stood at `4eafe58` with one commit above it, so
the written push list was stale again — the fourth session running in which that
happened. Everything else in the handoff held. The CRLF trap was confirmed still
present and still not a content change.

## Phase 1 — the ledger replication series

`backend/ledger_replication.py` executes the cadence D09 §4.5.4 already
specified: monthly full export, weekly incremental chained by
`previous_export_hash`, zero-record weeks kept rather than skipped, nothing ever
overwritten. `inspect` opens every bundle, recomputes its digest, verifies it
against its predecessor, and reports a missing period. 32 tests; the suite went
from 80 to 112. Commit `5ce18cd`; record in
`assets/ledger-replication-build-2026-11-10.md`.

**It deliberately transmits nothing.** D09 §3.2 promises the Platform has no
outbound network, so off-box carriage stays the Railroad's physical step under
§3.3. The owner chose on-box scheduling plus physical carriage over a network
push on 2026-11-10 — the alternative would have meant contradicting a
customer-facing commitment in order to close a control gap. Both docket rows
(B01 §7 item 12, D09 §4.4) now say carriage remains open instead of implying
replication is finished.

**Two audits found nine material defects before this was called built.** The
release verifier rejected every legitimate chained export; `inspect` never
opened a bundle, so tampering read as "continuous"; the period walker hung
forever on a 53-week ISO year (2026 is one); `due_exports` read state outside
the lock so concurrent runs duplicated bundles; and one test passed only because
the check it guarded had been deleted. A green suite of 108 preceded all of it.

## Phase 2 — the model decision, and the 29× defect under it

The owner delegated the A1-versus-D08 question ("you decide"). **A1 governs**, as
Option D in `assets/a2-d08-model-decision-2026-11-09.md`. Commit `58bfaef`.

A2 §3.2 and D08 §3 now state **1.77× at 500 axles, 3.36× at 10,000** with the
cost basis written into the sentence rather than left to inference, plus the
**1.65× / 3.34×** fallback for a basis that also disallows the conversion credit.

D08 §5–§6 were restated from A1, and the restatement surfaced something the old
headline hid. **D08 §2 scopes the pilot at 100–200 axles**; the old §5 computed a
pilot-year benefit at 500. At 200 axles A1 gives $278,670 against a $370,000
fee — **0.75×. The pilot does not pay for itself at its own scoped fleet size**,
and the document now says so in those words. Production years at 500 axles:
$696,675/yr. Four-year return 2.01×; six-year 2.06× — close to flat, because fee
escalation from Year 4 nearly cancels the dilution of one weak pilot year.

**`backend/roi.py` was valuing a missed defect 29× too high** — it carried a 2%
catastrophic-escalation probability where A1's B17 has held 0.05% since the first
correction, and blended the $9.25M severe-tier midpoint as though it were the
typical cost. It is now **$999,750**, arithmetically identical to A1's B22. The
NTSB benchmarks survive as `SEVERE_FAILURE_COST_*`, reference-only, and the
dataclass field was renamed `severe_cost_range_usd` so no later reader mistakes
them for the typical case.

## The lesson this session added

**The ROI test could not fail.** It rebuilt its expected value from the same
constants it then compared against:
`expected = (1 - roi.P_CAT) * roi.TYPICAL + roi.P_CAT * roi.CATASTROPHIC`,
asserted equal to `roi.EXPECTED_COST_PER_MISSED_DEFECT_USD`, which *is* that
expression. Restoring the 2% defect produced **112 passed, 0 failed**. It now
asserts literals; the same mutation gives 111 passed, 1 failed.

Third session running in which an audit found a test passing for the wrong
reason, and the second in which the faulty test was one I had just written. The
rule that follows is already in memory: assert literals, then break the thing
deliberately and confirm red.

## Nine audit findings, fixed before commit

A2 §3.2 claimed its figure needed "no conversion credit" when 1.77× requires one;
the "CLOSED" block printed pre-restatement totals while checking nothing; two
internal assets still carried the withdrawn model; A2 §9 ran the pilot at 500
axles; D08 §4's $1,390,000 was a rounded figure $289.50 light, replaced with the
derived $1,399,650; a "five years" heading sat over a six-year table; A1's
builder said "~2.0×" while its cell computed 2.2546×; and two more of the same
shape in the checkers.

## The workbook — rebuilt, not installed

The corrected A1 workbook was built and recalculated with LibreOffice: pilot year
**$370,000** (was $285,000, omitting two A2 lines), three-year ROI **2.0653×**.
It could not replace the original because **Excel held a lock on it** — copy,
delete and move all failed with Permission denied even after
`allow_cowork_file_delete`, because the lock is the host application and not a
sandbox permission. The rebuilt file therefore sits beside the original with
`REPLACE-WORKBOOK.bat` to swap it in.

**Until that runs, the committed `.xlsx` is stale** — it still carries the
$285,000 pilot year, and A2 §5.1 charges $370,000. This is the one
owner-action item blocking a clean close.

## Close of chat-4

Transcript extracted at 420 turns (4 user, 421 assistant after the closing
exchange) into `project-logs/transcripts/2026-11-10-chat-4.md`, with the raw log
at `project-logs/transcripts/raw/2026-11-10-chat-4-snapshot.jsonl` (9.9 MB,
4,322 events, 535 turns). The extractor's hard-coded `# Chat-3` heading was replaced with a
title derived from the output filename so it cannot mislabel a session again.

Build history regenerated at 34 pages. Part VII was rewritten rather than left
alone: it still described Findings 1 and 2 as open, which had been true when
written in chat-3 and stopped being true in phase 2 of this session. That is the
same defect class the document records elsewhere — a claim that was true when
written and never revisited when the evidence moved.

Verification at close: **113 tests, 97 arithmetic checks, 65 decision-paper
checks — all green.**
