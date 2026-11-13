# Chat-12 — Carry-Forward

**State at rollover:** suite **398 passed, 0 failed**. Working tree clean at close.
**Fourteen commits are unpushed** — the sandbox cannot reach GitHub. Verify with
`git log --oneline origin/main..HEAD` and push with `PUSH-TO-GITHUB.bat`. No hash
is written here, because a hash in a file is stale the moment it is committed.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `assets/chat-11-phase-record-2026-11-13.md`
4. `assets/asymmetric-signature-decision-2026-11-13.md` — **the one document that
   changes what the next chat does**

---

## What chat-11 changed

| Commit subject | Effect |
|---|---|
| Write down the Master % Tracker rubric | The gap-row bucket had no reproducible basis since chat-9. Now 64/120 = 16.0, total **78.4**, not the 79.1 carried in chat-10 |
| B04 described 2,695 lines of an 8,200-line codebase | Seven backend modules added to the inventory; supply-chain rows moved to the three-state wording. New `tests/test_b04_inventory.py` |
| Decide asymmetric signing for bundles, and correct D10 | The decision paper, plus D10 Part 5's false "key is issued and published" |
| B02 §9 said the ingest path was not built at all | Corrected; it contradicted B02's own §2. New `tests/test_docket_currency.py` |

---

## The three sentences that matter most for chat-12

1. **A capability gets built and the documents describing its absence do not
   close with it.** Chat-11 found two instances in different documents — B04
   (SBOM/signing "not produced" while tools existed) and B02 (ingest "not built at
   all") — after chat-9 and chat-10 had each fixed one by hand. The class is now
   mechanical: `tests/test_docket_currency.py` holds six capabilities and fails if
   any document asserts one is absent. **When a gap closes, add it to that list.**
2. **Staleness runs in both directions.** The sweep was hunting *absence* claims;
   D10's false *presence* claim ("the key is issued and published") was found only
   by an adversarial audit. A grep for "not built" will never find a document that
   claims too much.
3. **Two invented numbers were caught in the chat that wrote a paper about
   invented numbers.** The opening Master % figure (16.4, underived) and "49 tests"
   in the B02 correction (files said 43). Naming the habit does not cure it.
   **Derive, then write. Prefer a test over a memory.**

---

## Next ladder — low to high, one at a time

1. **The dashboard has never been seen.** *(low, owner action)* Unchanged from
   chat-10 and still true. Open `http://127.0.0.1:8420/` with
   `python3 -m backend.main` and look at it. Nothing in this environment renders;
   13 structural checks passing says nothing about appearance. This has now
   carried across two chats — it is the cheapest unclosed item in the project.

2. **The `gnupg` decision.** *(low to decide, blocks medium work)*
   `assets/asymmetric-signature-decision-2026-11-13.md` recommends detached GPG over
   export bundles and needs the owner to accept `gnupg` **and `dirmngr` — a daemon
   that performs network fetches** — into an image whose proposition is zero
   outbound network. One line of Dockerfile; the work is the CISO paragraph. Until
   this is answered, the asymmetric build cannot start.

3. **Benchmark the two invented numbers.** *(low)* The decision paper estimates a
   gpg signature at tens-to-hundreds of ms and assumes a disposition rate. Neither
   is measured. Both decide the per-row-versus-per-bundle scope. Cheap to do on any
   host with `gpg`.

4. **Sweep for stale claims in the other direction.** *(medium)* Grep the docket
   for statements that a thing **exists, is applied, or is issued** and check each
   against the code — the D10 defect's shape. `grep -rn "is issued\|is applied\|is
   published\|has been signed\|is complete"`.

5. **Real detector payload schema** *(medium — **blocked on the Railroad**)*.

6. **Apply the supply-chain tools** *(high — **blocked**)*. Needs a release host
   with index access and a GPG key under written custody. All three tools exist and
   are tested; none is applied.

7. **D07 §14.5 — governing law, seat and forum** *(counsel, not engineering)*.

**Do not open chat-12 by assuming there is code to write.** Items 1–3 are an owner
action, a product decision and a measurement. Items 4 is a sweep. Only item 4
produces a commit, and it may produce none.

---

## Master % Tracker at chat-11's close

Basis: 37 docket IDs (40) + 12 B01 §7 gap rows (30) + 8 software components (20) +
5 release gates (10). **Rubric and per-row scoring:**
`assets/master-tracker-rubric-2026-11-13.md`.

| Bucket | Weight | Chat-11 open | Close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

**Zero movement is the correct reading.** Nothing moved from "built, not applied"
to "applied", which is the only transition that moves this matrix. The suite rose
390 → 398; that is a better test suite, not a better product.

**Re-derive at chat-12's open rather than quoting 78.4.** Chat-10 quoted 79.1
having inherited it; chat-11 opened by adjusting it to 78.8 from impression and
only later derived 78.4. The rubric exists so this stops happening.

---

## Standing instructions, unchanged

- All project work written **directly into `C:\Users\RGV\AxiomDynamics`**, first
  pass, committed in the same pass. No drafts in the sandbox.
- **Verify against the file, then write.** Never cite from memory.
- **125K tokens per chat.** At the cap, alert and roll over.
- **Every build phase opens with a low→high priority ladder**, worked one item at
  a time.
- **Report the Master % Tracker Completion Matrix** at a phase's open and close,
  derived from a written rubric.
- **Independent adversarial audit** when I author both the artifact and its
  checker. Fresh agent, told to *falsify*. **It earned its keep in chat-11** —
  eight defects in the decision paper, four material, including a misattributed
  quotation and a false cost claim.
- **Never `git add -A`.** Stage named files; check with `--ignore-cr-at-eol`.
- **Never `git checkout -- <file>`.** Use `/tmp` or copy-and-restore.
- Extract and commit the transcript at close, raw `.jsonl` included, snapshot taken
  *after* the last exchange.

---

## Environment traps — updated

- **Use `tools/eol_edit.py` for every docket edit.** It reads bytes, detects the
  target's own ending, writes it back. **A multi-line old/new block can fail to
  match** (chat-11 hit this twice on B04 §7) — row-by-row single-line edits are
  more reliable. Use `--show-ending` first: the docket is mixed (B02 is LF, B04
  and D10 are CRLF), so never assume.
- **Assert a mutation landed before believing the run.** Chat-11 grepped for the
  mutated string and printed the match count each time. A silent no-op mutation
  proves nothing.
- **A guard that skips on a substring will fail on its own retraction.** The B02
  cross-section check tripped on the corrected paragraph because a retraction
  quotes the phrase it retracts. Narrow the rule to unretracted assertions.
- **`python3 -I -X pycache_prefix=/tmp/<dir>`** for every run; `-I` alone discards
  `PYTHONPYCACHEPREFIX`. **The full suite takes ~4–5 minutes** — `timeout_ms`
  ≥ 500000, or it dies at 120s and leaves an `index.lock`.
- **`git commit` leaves stale locks on this mount** (`index.lock`, `HEAD.lock`,
  `objects/*/tmp_obj_*`) even when it succeeds. `rm -f .git/*.lock` after each
  commit; if `rm` is refused, `allow_cowork_file_delete` with the **VM path** first.
- **`AXIOM_DB_PATH` before importing `backend.main`** — the import runs
  `store.init_db()` against the repo root.
- **The AxiomDynamics folder is not mounted at a fresh session's open.** Call
  `request_cowork_directory` with `C:\Users\RGV\AxiomDynamics` before anything else.
- A file in `project-logs/transcripts/raw/` cannot be overwritten in place; write
  fresh and `mv -f` over it.

---

## Push state

`git log --oneline origin/main..HEAD` is the only answer that counts. At chat-11's
open it was 9; four commits were added during the chat, so it is 13–14 depending on
the close commits. The sandbox cannot reach GitHub — `git push` and `git fetch`
both fail HTTP 403 from the proxy — so run `PUSH-TO-GITHUB.bat` from the repo root.
