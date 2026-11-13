# Chat-9 — Carry-Forward

**State at rollover:** suite **370 passed, 0 failed**. Working tree clean at
close. **Three commits are unpushed** — the sandbox cannot reach GitHub, so
verify with `git log --oneline origin/main..HEAD` and push with
`PUSH-TO-GITHUB.bat`. No hash is written here, because a hash in a file is stale
the moment it is committed.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `project-logs/chat-9/SUMMARY.md`
4. `assets/attestation-at-entry-build-2026-11-13.md`

---

## What chat-9 changed

| Commit subject | Effect |
|---|---|
| Stage 12 + three stale gating claims | Build history caught up to chat-8; three documents stopped saying entry was ungated |
| Require an attestation at entry | Disposition row cannot exist unattested; suite 359 → 370 |
| Build history Stage 13 | 46 pages, stages 0–13 |

**The single most important sentence for chat-10:** two layers of one check
cannot both be tested through the outer layer. Three of six mutations survived
because every test entered through the route's early check and never reached the
transactional one. When a guard has a twin, test each at its own boundary.

---

## Next ladder — low to high, one at a time

**The buildable queue inside this repository is close to empty. That is the
honest state, not an understatement.**

1. **`D00` Part II status sweep and `CURRENT-STATE.md` refresh** *(low)*.
   D00's Part V still says "Built — 36 Markdown… Not yet built — 0" which is
   true, but Part VI's gap rows and the `B01 §7` item-1 row both need to reflect
   that attestation is now required at entry rather than optional. Verify each
   against the code before editing; do not carry a claim from this file.
2. **The signed key directory has the same asymmetric limit as everything
   else** *(medium)*. It proves the export-key holder authored the bindings, not
   that they were entitled to. This is the same defect as item 11 and closing it
   properly means **an asymmetric signature** — stdlib has none, so it is a
   dependency decision (D10 / D09 §4.4) before it is a code decision. Do not
   start it without deciding the dependency, or it becomes a hand-rolled
   primitive in a product that tells CISOs it does not hand-roll crypto.
3. **Real detector payload schema** *(medium — **blocked on the Railroad**)*.
   Item 5's authentication half closed in chat-7. The schema must be agreed with
   them before it can be written. Nothing in the repository can advance this.
4. **Apply the supply-chain tools** *(high, Q1–Q2 2027 targets)*. SBOM, hash
   pinning and GPG signing are **built, not applied**. This is a release-process
   change needing a host with index access and a GPG key with written custody —
   not a code change, and not doable from this sandbox.
5. **D07 §14.5 — governing law, seat and forum** *(counsel, not engineering)*.
   Blocks first execution.

---

## Master % Tracker at chat-9's close

Basis: 37 docket IDs (40 pts) + 12 B01 §7 gap rows (30) + 8 software components
(20) + 5 release gates (10).

| Bucket | Weight | Chat-9 open | Close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 13.1 | 15.6 | +2.5 |
| Core software (8) | 20 | 13.3 | 15.8 | +2.5 |
| Release readiness (5) | 10 | 3.0 | 3.0 | — |
| **Total** | **100** | **69.4** | **71.9** | **+2.5** |

Derive these from the files at the start of chat-10 rather than quoting them —
a percentage carried in a handoff is stale the first time a document is edited.

---

## Standing instructions, unchanged

- All project work written **directly into `C:\Users\RGV\AxiomDynamics`**, first
  pass, committed in the same pass. No drafts in the sandbox.
- **Verify against the file, then write.** Never cite from memory.
- **125K tokens per chat.** At the cap, alert and roll over.
- **Every build phase opens with a low→high priority ladder**, worked one item at
  a time.
- **Report the Master % Tracker Completion Matrix** at a phase's open and close.
- **Independent adversarial audit** when I author both the artifact and its
  checker. Fresh agent, told to *falsify*.
- **Never `git add -A`.** Stage named files; check with `--ignore-cr-at-eol`.
- **Never `git checkout -- <file>`.** Use `/tmp` or the driver's `--restore`.
- Extract and commit the transcript at close, raw `.jsonl` included, snapshot
  taken *after* the last exchange.

---

## Environment traps — all hit again in chat-9

- **A stale `.git/index.lock`** appears when a tool call is interrupted mid-git
  operation. `git add` then dies with "Unable to create index.lock". Fix:
  `allow_cowork_file_delete` with the **VM path**
  (`/sessions/<session>/mnt/AxiomDynamics/.git/index.lock`), then `rm`.
- **A `python3 - <<'PY'` rewrite converts CRLF to LF**, turning a one-line edit
  into a 167-line diff. `git diff --cached --ignore-cr-at-eol` collapses it back
  and proves it is endings, not content. The fix that works: a helper that reads
  bytes, detects `\r\n`, and writes the **same** ending back. Use it for every
  docket edit.
- **The mutation driver leaves the tree mutated if interrupted.** Chat-9 hit
  this: `backend/ingest_auth.py` was left with M8 applied (`if False:` where
  `if dup is not None:` belonged). Check `git diff --ignore-cr-at-eol -- backend/`
  after any interrupted run, and restore by hand — never `git checkout --`.
- **The build-history generator prints `register failed: OperationalError`**
  twice. That is `test_issue_reviewer_key` exercising the seeder's refusal path
  inside `execSync("python3 -I tests/run_tests.py")`. Pre-existing and harmless;
  the docx still writes. Do not "fix" it without checking it is not hiding a
  real failure.
- **Importing `backend.main` runs `store.init_db()`** against the repo root. Set
  `AXIOM_DB_PATH` **before** the backend import.
- **A file in `project-logs/transcripts/raw/` cannot be overwritten in place.**
  Write fresh and `mv -f` over it.

---

## Push state

`git log --oneline origin/main..HEAD` is the only answer that counts. At chat-9's
open that count was 0; three commits were added during the chat. The sandbox
cannot reach GitHub — `git push` and `git fetch` both fail HTTP 403 from the
proxy — so run `PUSH-TO-GITHUB.bat` from the repo root.
