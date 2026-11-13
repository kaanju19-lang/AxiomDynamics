# Chat-10 — Carry-Forward

**State at rollover:** suite **390 passed, 0 failed**. Working tree clean at
close. **Eight commits are unpushed** — the sandbox cannot reach GitHub, so
verify with `git log --oneline origin/main..HEAD` and push with
`PUSH-TO-GITHUB.bat`. No hash is written here, because a hash in a file is stale
the moment it is committed.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `assets/frontend-enterprise-pass-2026-11-13.md`
4. `tests/test_frontend.py` — the 13 checks, if the next rung touches the UI

---

## What chat-10 changed

| Commit subject | Effect |
|---|---|
| Sweep the attestation claims chat-9 left stale | Four documents corrected; `close-gate.sh` gained a guard for the phrasing that hid them; suite 370 → 377 |
| Enterprise dashboard pass | Measured palette, 13-symbol vector sprite, no colour-only state, keyboard-reachable rows; suite 377 → 390 |

**The single most important sentence for chat-11:** *a gate that greps one
phrasing of a claim only catches that phrasing.* Chat-9 wrote a close-gate guard
for "entry is ungated" and it worked — and four documents still said entry
needed no attestation, phrased "but not an attestation". When a gap closes, grep
for every way the old state could be worded, not the way it was worded in the
document that prompted the guard.

---

## Next ladder — low to high, one at a time

1. **The dashboard has never been seen.** *(low, owner action)* Open
   `http://127.0.0.1:8420/` with `python3 -m backend.main` and look at it. There
   is no browser in the sandbox and the preview panel does not open, so every
   claim about how it *looks* is unverified. Structural tests pass; appearance
   does not follow from them. Expect to want spacing and density changes.

2. **A screenshot-based visual regression check** *(medium)*. Item 1 is manual
   because nothing here renders. If the owner wants the UI held to a standard
   across chats, that needs a renderer available (a headless browser on the
   owner's machine, or a checked-in reference screenshot the owner approves).
   Do not pretend the current suite covers this.

3. **The asymmetric-signature decision paper** *(medium — D10 / D09 §4.4)*.
   Unchanged from chat-9's ladder and still the highest-value unblocked item.
   B01 §7 items 1 and 11, and the signed key directory's limit, are all the same
   defect: a symmetric signature cannot name or bind an author. Stdlib has no
   asymmetric primitive, so this is a **dependency decision before it is a code
   decision**. Writing it must not smuggle in a hand-rolled primitive in a
   product that tells CISOs it does not hand-roll crypto.

4. **Real detector payload schema** *(medium — **blocked on the Railroad**)*.

5. **Apply the supply-chain tools** *(high)*. SBOM, hash pinning and GPG signing
   are built, not applied. Needs a release host with index access and a GPG key
   under written custody.

6. **D07 §14.5 — governing law, seat and forum** *(counsel, not engineering)*.
   Blocks first execution.

---

## Master % Tracker at chat-10's close

Basis: 37 docket IDs (40 pts) + 12 B01 §7 gap rows (30) + 8 software components
(20) + 5 release gates (10).

| Bucket | Weight | Chat-10 open | Close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.7 | 16.7 | — |
| Core software (8) | 20 | 17.9 | 20.0 | +2.1 |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **77.0** | **79.1** | **+2.1** |

**Note the re-base, because it matters more than the number.** Chat-9's close
read 71.9; chat-10's open read 77.0 with nothing built in between. That was a
rubric change, not progress: chat-9 appears to have scored "tool built, not
applied" higher than the exit condition supports. Chat-10 opened at its own
re-derived figure and disclosed the difference rather than carrying 71.9 forward
and reporting +7.2 of phantom movement. **Derive these from the files at the
start of chat-11 rather than quoting them.** A percentage carried in a handoff
is stale the first time a document is edited.

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

## Environment traps — updated

- **Use `tools/eol_edit.py` for every docket and frontend edit, and for every
  mutation that edits a file in place.** It reads bytes, detects the target's own
  ending, and writes it back unchanged. Chat-10 hit the trap twice: once when a
  `python3` heredoc stripped CRLF from three frontend files, and once when a
  mutation's LF needle silently failed to match a CRLF file, so the mutation
  never applied and the "surviving mutant" proved nothing. **Always assert that a
  mutation actually landed before believing what the test run says about it.**
- **`style.css` is now uniformly CRLF** (it was mixed, 603 CRLF / 80 LF, before
  chat-10). `index.html` and `app.js` are CRLF. Docket `.md` files are LF. Check
  with `tools/eol_edit.py <file> --show-ending`.
- **A stale `.git/index.lock`** appears when a tool call is interrupted mid-git
  operation — chat-10 hit it from a close-gate run that timed out. Fix:
  `allow_cowork_file_delete` with the **VM path**
  (`/sessions/<session>/mnt/AxiomDynamics/.git/index.lock`), then `rm`.
- **The live session log is at**
  `/sessions/<session>/mnt/.claude/projects/session/*.jsonl` — pick the newest by
  mtime. `close-gate.sh` derives it; do not hardcode the id.
- **The full suite takes ~4–5 minutes.** Any bash call that runs it needs
  `timeout_ms` of at least 500000, or it dies at 120s and leaves an
  `index.lock` behind. Pass `-X pycache_prefix=/tmp/<dir>` explicitly; `-I`
  discards `PYTHONPYCACHEPREFIX`.
- **Importing `backend.main` runs `store.init_db()`** against the repo root. Set
  `AXIOM_DB_PATH` **before** the backend import.
- **The build-history generator prints `register failed: OperationalError`**
  twice. Pre-existing and harmless; the docx still writes.
- **A file in `project-logs/transcripts/raw/` cannot be overwritten in place.**
  Write fresh and `mv -f` over it.

---

## Push state

`git log --oneline origin/main..HEAD` is the only answer that counts. At chat-10's
open that count was 6; two commits were added during the chat, so it is 8. The
sandbox cannot reach GitHub — `git push` and `git fetch` both fail HTTP 403 from
the proxy — so run `PUSH-TO-GITHUB.bat` from the repo root.
