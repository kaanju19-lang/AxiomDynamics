# Chat-5 — Carry-Forward

Handoff from chat-4, closed 2026-11-10. Read this first, then confirm every
claim below against the repository. **Nothing in this document is authority.**
The repository is. Every written push list in this project has gone stale at
least once — four sessions running now, including this one's.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md` — what is built, what is pushed, what is open.
2. This file — where chat-4 stopped and what it left waiting.
3. `project-logs/chat-4/SUMMARY.md` — the reasoning behind each phase.
4. `project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx` — 34
   pages, the whole build, readable cold. Regenerate it with
   `node project-logs/build-history-summary.js` after any material change; do
   not hand-edit the .docx.
5. `client-assets/MASTER-BRIEF-DOCKET/D00-DOCKET-INDEX.md`, Part IV and Part VI —
   the authority on docket status and the gap register.

## Confirm state, do not assume it

```bash
git log --oneline -8                            # where chat-4 stopped
git log --oneline origin/main..HEAD             # what is actually unpushed
git diff --ignore-cr-at-eol --stat              # real changes only
python3 -I tests/run_tests.py                   # 114 passed at close
python3 -I assets/a2-d08-arithmetic-pass.py     # 97 checks at close
python3 -I assets/a2-d08-model-decision.py      # 65 checks at close
```

**The line-ending trap.** `git status` lists nearly every tracked file as
modified on this checkout. It is CRLF working-tree content against LF blobs, not
content: `git diff --ignore-cr-at-eol` returns empty for those. There is no
`.gitattributes` and `core.autocrlf` is unset. Always check with
`--ignore-cr-at-eol`, stage named files only, and **never `git add -A`**.

## Two things that need the owner, before anything else

1. **`client-assets/MASTER-BRIEF-DOCKET/A1-ROI-MODEL/REPLACE-WORKBOOK.bat`** —
   after closing Excel. The rebuilt workbook is committed beside the old one
   because the old one was locked open in Excel and could not be replaced from
   here. **Until this runs, the committed `.xlsx` is stale**: its pilot year is
   $285,000 while A2 §5.1 charges $370,000, and its three-year ROI reads 2.25×
   against the rebuilt file's 2.0653×.
2. **`PUSH-TO-GITHUB.bat`** — the sandbox cannot reach GitHub (`git push` and
   `git fetch` both fail HTTP 403 from the proxy). Until it runs, everything is
   durable only on this disk.

**Check the queue with `git log --oneline origin/main..HEAD`; do not trust a
number written here.** The sandbox's `origin/main` ref is not evidence of what
the remote holds, because it cannot fetch.

## What chat-4 decided, and what it changed

**A1 governs the commercial numbers** — decided by me on the owner's delegation
("you decide"), expressed as Option D in
`assets/a2-d08-model-decision-2026-11-09.md`. Commit `58bfaef`.

- **A2 §3.2 / D08 §3:** 1.77× at 500 axles, **3.36× at 10,000** — the withdrawn
  2.0×/4.1× is gone. The basis is in the sentence, not inferred. Fallback
  **1.65× / 3.34×** if the conversion credit is disallowed. Do not mix bases in
  one table.
- **D08 §5–§6 restated from A1.** Pilot at the **200 axles §2 actually scopes**:
  $278,670 modelled benefit against the $370,000 fee — **0.75×. The pilot does
  not pay for itself, and the document now says so.** Production at 500 axles:
  $696,675/yr. Four years **2.01×**, six years **2.06×** — close to flat and
  should be read as flat.
- **`backend/roi.py`** now values a missed defect at **$999,750**, matching A1's
  B22. It was **29× too high**. The $5M/$13.5M NTSB figures survive as
  `SEVERE_FAILURE_COST_*`, reference-only.

**Two traps a reader will hit.** A2 §3.2 says 1.77× at 500 axles and D08 §5 says
2.01× on the same inputs — different questions, both now stated in the text (A2
charges the pilot with no benefit; D08 credits the 200-axle pilot's actual
benefit). And D08 §2 scopes the pilot at 100–200 axles, so any pilot-year benefit
computed at 500 contradicts the document's own scope — that was my defect, caught
before commit.

## A tenth defect found at validation — read this before touching the export

Nine defects came from two adversarial audits. The tenth came from *attacking the
artifact* when the owner asked that the completed tasks be validated, and it is
the most transferable of the set.

**A signed bundle accepted any extra top-level field.** Both verifiers returned
`ok=True` while an unsigned key rode along beside the four signed parts. The
signature covers a selected tuple and the digest names its fields; neither covers
"everything else". Such a key can be changed after signing without detection, and
a recipient would reasonably read it as attested. Both verifiers now reject it
with `bundle_no_extras`.

The design decision stands: signing a named field list is correct, because it
makes the covered set explicit in code. What was missing was the check that
nothing outside that set is present. If you change the bundle format, that check
has to change with it.

## The lesson chat-4 most wants carried

**A guard that recomputes its own expectation is not a guard.** The ROI test built
`expected` from the same constants it compared against, so it passed for any
values: restoring the 2% defect gave 112 passed, 0 failed. It now asserts
literals and is mutation-tested. Third session running that an audit found a test
passing for the wrong reason.

The second lesson is a habit, not a defect: **never `git checkout -- <file>` to
undo a test mutation.** Doing that wiped an hour of uncommitted edits to a
checker. Copy to `/tmp` first, or re-edit the line.

## The ledger replication series — built, audited, committed

`5ce18cd`. `backend/ledger_replication.py` produces the D09 §4.5.4 cadence and
verifies it; it deliberately transmits nothing, because D09 §3.2 promises no
outbound network, so carriage is the Railroad's physical step. Nine defects from
two audits are recorded in `assets/ledger-replication-build-2026-11-10.md`.

## What is still open — the real list

1. **D07 §14.5 — governing law, seat and forum.** Open counsel decision. Blocks
   first execution. Not a formation question; entity choice does not answer it.
2. **Signer attribution for the ledger.** The largest remaining code item and a
   genuine AD-2 dependency — real local accounts with a key per reviewer. It is
   much larger than it looks. Do not start here casually.
3. **Phase 0 formation**, if a real customer conversation is closer than a code
   milestone. Texas LLC, $300 filing, operating agreement worth paying for.
4. **Off-box carriage of the replication series** — open by design, the
   Railroad's physical step under D09 §3.3.
5. **SBOM, hash pinning of dependencies, signed releases** — Q1–Q2 2027 targets,
   all disclosed in D09 §4.4.

## The largest gap in the product, unchanged

**There is no detector ingest path.** No endpoint accepts a Railroad payload.
Every demonstration signal is generated from the physics equations on synthetic
traces. Disclosed in B01 §7 item 5, B02 §2, B03's status block. Every
demonstration number demonstrates the method, not the customer's data.

## Standing instructions, unchanged

- **All project work is written directly into `C:\Users\RGV\AxiomDynamics`, first
  pass, and committed in the same pass.** No drafts anywhere else. A whole phase
  was lost to sandbox storage in chat-1.
- **"We will keep this same concept throughout."** The physics-first framing, the
  document structure and the numbering discipline do not vary between documents.
- **"Strictly goes in our assets folder."** Internal analysis in `assets/`, never
  in `client-assets/`. Client-facing material is the docket only.
- **Verify against the file, then write.** Never cite from memory and check
  afterwards. Nearly every bad citation in this project came from that habit.
- **Extract and commit the session transcript at close, raw `.jsonl` included**,
  snapshot taken *after* the last exchange.
- **Independent adversarial audit** whenever I author both an artifact and its
  checker. Use a fresh agent instructed to *falsify*, not to confirm.
- **At 150K tokens in a chat, alert the owner and roll over to a new chat** — with
  the transcript, `CURRENT-STATE.md` and this file committed first. Added by the
  owner on 2026-11-10 after several sessions died of context exhaustion mid-task.

## Push required

`PUSH-TO-GITHUB.bat`, then confirm on the commits page. The command environment
cannot reach GitHub.
