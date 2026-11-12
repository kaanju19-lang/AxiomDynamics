# Chat-8 — Carry-Forward

**State at rollover:** suite **359 passed, 0 failed**. Nothing outstanding — the
owner pushed through `PUSH-TO-GITHUB.bat` during the chat and `origin/main`
moved to the last chat-8 commit by `update by push`. Verify with
`git log --oneline origin/main..HEAD`; **no hash is written here**, because any
hash in a file is stale the moment it is committed.

Chat-8 closed chat-7's four surviving mutations and wrote the AD-2 key custody
procedure. Between them those two jobs found **five defects that a green suite of
346 tests had not found** — two in the mutation driver, three in the product.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `project-logs/chat-8/SUMMARY.md`
4. `assets/mutation-survivors-closed-2026-11-11.md` (phase one)
5. `assets/key-custody-procedure-2026-11-11.md` (phase two)

---

## Phase one — the four mutation survivors

Commit **`a4ccc0b`**. Driver now reports **18 mutations, 18 killed, 0 survived**.
Suite 346 → 351.

| # | What was missing | Test added |
|---|---|---|
| M2 | No test compared the **error text**; only status and row count | `test_the_http_route_refuses_a_missing_or_bad_token_and_logs_nothing` asserts `"collector enrollment" in body["error"]` |
| M3 | Garbage body **with an unknown token** — the one shape where a row reaches the ingest log while the status stays 401 | `test_ingest_with_an_unknown_token_is_401_and_logs_nothing` |
| M5 | Nothing called the route function directly with `headers={}` | `test_the_route_refuses_a_missing_header_when_a_collector_is_enrolled` |
| M9 | The forged-append test tripped the **prev_hash** check, never the entry-hash check | `test_a_row_with_the_right_prev_hash_but_a_wrong_entry_hash_is_caught` |

**M2 was not the gap it was reported to be.** I first declared it an equivalent
mutant; an independent audit found the 401 *text* differs. I had compared status
and side effects and stopped there.

### Two defects in the driver, both of which would have produced false greens

- **An `EQUIVALENT` table keyed by mutation index.** The auditor substituted a
  genuine survivor into that slot and the driver printed "equivalent" and exited
  **0**. It would have absorbed any real survivor landing there. Removed
  entirely; a survivor now always prints `ALIVE`, with instructions to decide by
  reading the code and an explicit prohibition on index-keyed exemptions.
- **Pycache isolation was inert.** The suite runs under `-I`, and **`-I` sets
  `sys.pycache_prefix` to `None`**, discarding `PYTHONPYCACHEPREFIX`. Bytecode
  still reached the source tree. Now `-X pycache_prefix=<fresh tmp dir>`, which
  `-I` honours. Both claims verified empirically, both ways.

The driver also now removes a stale snapshot before writing one (a leftover
snapshot from an interrupted run would restore a *mutated* tree).

---

## Phase two — the AD-2 custody procedure (D09 §8.4)

Commit **`3de44cf`**; record corrections `1f1fce8`. Suite 351 → 359.

Eight subsections, placed in D09 beside §4.5 which already does the same job for
the export key — no new document, no new docket ID. 8.4.1 separates the three
credentials; 8.4.2–8.4.5 are joiner, mover, leaver, rotation in dependency order;
8.4.6 is the custody log (`key_id`, never the key); 8.4.7 forbids interchange
with the export key; 8.4.8 states the limits.

### Three product defects the procedure exposed, none found by a test

1. **A key could be registered to a second reviewer, and the second one won.**
   `register` refused only a key revoked *anywhere* in history. A *live* key
   presented under a different reviewer was accepted, and because `attest`
   resolves the **newest** entry for a `key_id` — deliberately, so renewal works
   — the second reviewer took the key over and the original holder was locked
   out of their own key. The register is append-only, so the bad binding could
   never be removed; `entries_consistent` caught it only at publish time.
   Now refused **at the write**. A renewal under a new certificate for the
   **same** reviewer still works — my first fix refused that too and would have
   broken rotation to fix sharing.
2. **A refused key directory still handed back bindings** — `{"ok": False,
   "bindings": {"<key>": "Hoffman"}}` for the directory it had just refused.
   Now `{}` on refusal.
3. **The procedure named a step nobody could perform.** The only code that made
   a reviewer key was `seed_demo_account.py`, which generates one and discards
   it. `tools/issue_reviewer_key.py` is the joiner step: generate, register,
   print the `key_id`, never the key, refuse to overwrite an existing key file.

Every mechanism claim in §8.4 was **executed** rather than reasoned about. Both
new guards are mutation-tested — each fails exactly one test when removed, and no
other. One more defect, in my own writing: the phase-two record put the B01 AD-2
bullet at "§10". B01 has no §10; the bullet sits in the unnumbered preamble.
Corrected before it was committed.

---

## Next ladder — low to high, one at a time

Both items below were offered at chat-8's close and neither is started.

1. **Regenerate the build-history docx for chat-8** *(low)*.
   `project-logs/build-history-summary.js` has stages 1–11; chat-8 is stage 12.
   The close gate asserts `Stage 11` is present, so that assertion must become
   `Stage 12` in the same edit or it will pin the document to a stale stage.
   Rebuild with node, then check: no literal `**` or backticks in the extracted
   text, and render to PDF and read the pages — the TOC field renders empty in
   converters that do not update fields.
2. **Attestation at entry** *(medium)*. Entry now requires a live session; it
   does not require an attestation, so an unattested row is still possible. This
   changes `POST /api/warrant/<id>/disposition` and its tests. It does **not**
   close item 1 — a key holder is not a person.
3. **The real payload schema** *(medium, blocked on the Railroad)*. Item 5's
   authentication half closed in chat-7; the schema must be agreed with them
   before it can be written.
4. **Apply the supply-chain tools** *(high, Q1–Q2 2027 targets)*. SBOM, hash
   pinning and GPG signing are **built, not applied**. Applying them is a
   release-process change, not a code change.
5. **D07 §14.5 — governing law, seat and forum** *(counsel, not engineering)*.
   Blocks first execution.

---

## Standing instructions, unchanged

- All project work written **directly into `C:\Users\RGV\AxiomDynamics`**, first
  pass, committed in the same pass. No drafts in the sandbox — a whole phase was
  lost that way.
- **Verify against the file, then write.** Never cite from memory.
- **125K tokens per chat.** At the cap, alert and roll over.
- **Every build phase opens with a low→high priority ladder**, worked one item at
  a time.
- **Independent adversarial audit** whenever I author both the artifact and its
  checker. Fresh agent, told to *falsify*.
- **Never `git add -A`.** Stage named files; check with `--ignore-cr-at-eol`.
- **Never `git checkout -- <file>`.** Use `/tmp` or the driver's `--restore`.
- Extract and commit the transcript at close, raw `.jsonl` included, snapshot
  taken *after* the last exchange.

### Two environment traps confirmed in chat-8

- **Importing `backend.main` runs `store.init_db()`** against the repo root. A
  test that imports it before setting `AXIOM_DB_PATH` creates an `axiom.db` there
  and dies with `disk I/O error` on this mount. Set the env var **before** the
  backend import.
- **A file in `project-logs/transcripts/raw/` cannot be overwritten in place**
  once created — `cp` onto it and `>>` to it both return `Permission denied`.
  Write to a fresh name in the same directory and `mv -f` over it. The extractor
  script copies with `shutil.copyfile`, so give it a `/tmp` destination and move
  the file in afterwards.

---

## Push state

`git log --oneline origin/main..HEAD` is the only answer that counts. At chat-8's
close that count was **0** and `git reflog show origin/main` records
`update by push`. The sandbox cannot reach GitHub — `git push` and `git fetch`
both fail HTTP 403 from the proxy — so anything committed *after* this file is
pushed by running `PUSH-TO-GITHUB.bat`.
