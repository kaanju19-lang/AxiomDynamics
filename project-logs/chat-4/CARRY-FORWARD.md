# Chat-4 — Carry-Forward

Handoff from chat-3, closed 2026-11-10. Read this first, then confirm every
claim below against the repository. **Nothing in this document is authority.**
The repository is. Every written push list in this project has gone stale at
least once, including three in chat-3's own record.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md` — what is built, what is pushed, what is open.
2. This file — where chat-3 stopped and what it left waiting.
3. `project-logs/chat-3/SUMMARY.md` — the reasoning behind each phase.
4. `project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx` — 32
   pages, the whole build, readable cold. Regenerate it with
   `node project-logs/build-history-summary.js` after any material change; do
   not hand-edit the .docx.
5. `client-assets/MASTER-BRIEF-DOCKET/D00-DOCKET-INDEX.md`, Part IV and Part VI —
   the authority on docket status and the gap register.

## Confirm state, do not assume it

```bash
git log --oneline -8                            # where chat-3 stopped
git status --short --branch                     # how far ahead of the remote ref
git log --oneline origin/main..HEAD             # what is actually unpushed
git diff --ignore-cr-at-eol --stat              # real changes only
python3 -I tests/run_tests.py                   # 80 passed, 0 failed at close
```

**The line-ending trap.** `git status` lists nearly every tracked file as
modified on this checkout. It is CRLF working-tree content against LF blobs, not
content: `git diff --ignore-cr-at-eol` returns empty for those. There is no
`.gitattributes` and `core.autocrlf` is unset. Always check with
`--ignore-cr-at-eol`, stage named files only, and **never `git add -A`**.

## Push required before anything else

The command environment cannot reach GitHub — `git push` and `git fetch` both fail
with HTTP 403 from the proxy. Chat-3 ended with commits local and unpushed on top
of a remote ref of `bb99cdd`. The owner pushes with `PUSH-TO-GITHUB.bat` in the
repo root, and then confirms on the commits page. Until that happens, none of it
is durable anywhere but this disk.

## What chat-3 built

Four substantive phases and a transcript phase. Full reasoning in
`chat-3/SUMMARY.md`; the short version:

- **The append-only disposition ledger** (`209efe6`) — insert-only writes,
  `supersedes_id` corrections, `BEFORE UPDATE`/`BEFORE DELETE` triggers, SHA-256
  chain, `BEGIN IMMEDIATE`. Fixed a code defect where a second decision on an
  advisory silently destroyed the first. 17 tests.
- **The A2/D08 decision paper** (`b23d0c7`) — prices both answers to the two
  modelling findings, so the decision is a comparison rather than more research.
  65 checks. No product code changed.
- **The signed ledger export** (`d9c83d4`) — HMAC-SHA256 bundle,
  `backend/ledger_export.py` plus a standalone verifier in `tools/` that imports
  nothing from `backend/`. 42 tests. The second half of AD-3.
- **The transcript machinery** (`53ad93a`) — `project-logs/extract_transcript.py`,
  the readable extract and the raw `.jsonl`, re-snapshotted at the actual close.

## The decisions waiting, in order of consequence

1. **Which model governs the commercial numbers** — A1's probability-blended
   evaluation (0.05% escalation, $500,000 typical cost) or D08 §5–§6's
   contained-tier basis. Everything quoted to a customer depends on it. Options
   costed in `assets/a2-d08-model-decision-2026-11-09.md` §6–§7; the
   recommendation is A1. **This is the only blocking item that needs the owner.**
2. **Whether to strike or restate the 2.0×/4.1× return anchors** in A2 §3.2 and
   D08 §3. The decision paper showed they *are* recoverable on an unstated cost
   basis (p between 0.04% and 0.07%, horizon unspecified), which makes this a
   disclosure question, not a fabrication question. They cannot ship until a
   frame is stated.
3. **Then regenerate the A1 workbook** from the corrected builder and re-run both
   check scripts. Deliberately not done — regenerating bakes the undecided model
   into a new file.
4. **D07 §14.5 — governing law, seat and forum.** Open counsel decision. Blocks
   first execution. Not a formation question.
5. **Phase 0 formation**, if a real customer conversation is closer than a code
   milestone. Texas LLC, $300 filing, operating agreement worth paying for.

## The nearest build, if the decision stays deferred

**Off-box replication of the ledger.** The export exists and is signed; nothing
ships it on a schedule, so a lost disk still loses the ledger. B01 §7 item 12,
D09 §4.4–4.5. It is the last item in that gap list that needs no commercial
decision and no new dependency.

Do **not** start with signer attribution. That is a genuine AD-2 dependency —
real local accounts with a key per reviewer — not more export code, and it is a
much larger piece of work than it looks.

## The largest gap in the product, unchanged

**There is no detector ingest path.** No endpoint accepts a Railroad payload.
Every demonstration signal is generated from the physics equations on synthetic
traces. Disclosed in B01 §7 item 5, B02 §2, B03's status block. Every
demonstration number demonstrates the method, not the customer's data.

## Standing instructions, unchanged

- **All project work is written directly into `C:\Users\RGV\AxiomDynamics`, first
  pass, and committed in the same pass.** No drafts anywhere else.
- **"We will keep this same concept throughout."** The physics-first framing, the
  document structure and the numbering discipline do not vary between documents.
- **"Strictly goes in our assets folder."** Internal analysis in `assets/`, never
  in `client-assets/`. Client-facing material is the docket only.
- **Verify against the file, then write.** Never cite from memory and check
  afterwards. Nearly every bad citation in this project came from that habit.
- **Extract and commit the session transcript at close, raw `.jsonl` included.**
  Take the snapshot *after* the last exchange, not before it.
- **Independent audit for anything that makes a security claim.** When I write
  both an artifact and its checker, a second agent tries to falsify it. Chat-3
  produced two examples of why: a total-wipe attack that verified green, and a
  document that stated a figure appearing nowhere in the repository.

## The one lesson chat-3 would most like carried forward

Three of chat-3's phases were changed by an audit that found what the author had
not thought of. The pattern in all three is identical: **the work was internally
consistent and externally wrong.** A test suite written by the author of a
mechanism tests the author's model of the threat. A document written from one
reading of the code agrees with that reading. The fix is not more care — it is a
reader with no stake in the conclusion.

It has now earned its cost three times in two sessions. Budget for it.
