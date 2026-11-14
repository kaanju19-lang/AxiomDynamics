# Chat-13 — Carry-Forward

**State at rollover:** suite **402 passed, 0 failed**. Working tree clean at close.
The local `origin/main` tracking ref equals `HEAD` at close, so the chat-12 work
appears pushed — but **the sandbox cannot reach GitHub**, so confirm with
`git log --oneline origin/main..HEAD` and check the commits page. No hash is
written here, because a hash in a file is stale the moment it is committed.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `assets/chat-12-phase-record-2026-11-13.md`
4. `assets/gpg-benchmark-2026-11-13.md` — the measurement, and the two corrections
   the audit forced into it

---

## What chat-12 changed

| Commit subject | Effect |
|---|---|
| Measure the two invented numbers, and stop D09 promising an admin purge | Signature cost measured; disposition rate traced to B01 §6; D09 §5.2's admin-interface claim corrected |
| Set WAL, which four docket statements have claimed since chat-3 | `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout=30s` on every ledger connection; `timeout=30` on the two atomic helpers |
| Repair what the audit of chat-12 found, including a fix I claimed but did not make | Nine defects; the worst was a commit message asserting a fix the diff did not contain |

---

## The three sentences that matter most for chat-13

1. **A commit message is a claim and can be false.** `70077a8` said the D09
   termination sentence was corrected. It sat three lines below the paragraph
   announcing its removal, unedited, still citing D07 §15.5 for an obligation
   §15.5 does not contain. Only the adversarial audit found it. **Verify the
   message against the diff before committing, not after.**
2. **A right number with a wrong mechanism is more dangerous than a wrong
   number.** The 299 ms reproduced; "gpg-agent plus pinentry startup" did not.
   The auditor isolated it to iterated S2K three ways. The number survives
   checking and carries the explanation with it.
3. **A guard that cannot fail is worse than no guard, because it gets cited.**
   Three checks in `test_docket_currency.py` passed their own tests and could
   not fail: bare-word skip tokens, two literal route names, a filename nothing
   produces. **When you write a guard, construct the input that should trip it
   and confirm it does.**

---

## Next ladder — low to high, one at a time

1. **The dashboard has never been seen.** *(low, owner action)* **Four chats.**
   `python3 -m backend.main`, then `http://127.0.0.1:8420/`. Also
   `frontend/render/panel.html`, committed 2026-11-13 with "not yet verified
   visually" in its own message. This environment has no renderer — confirmed
   twice in chat-12 — so nothing here can check it.

2. **The `gnupg` decision.** *(low to decide, blocks medium work)*
   `assets/asymmetric-signature-decision-2026-11-13.md` recommends detached GPG
   over export bundles and needs the owner to accept `gnupg` **and `dirmngr` — a
   daemon that performs network fetches** — into an image whose proposition is
   zero outbound network. **Chat-12 removed the cost objection** (signing is
   0.65 s/year at 64 bundles) and left this one exactly where it was. It is
   commercial, not engineering.

3. **The rubric's existence-versus-accuracy gap.** *(low to decide)* The
   docket-documents bucket scores 37 documents *existing*. Chat-12 corrected five
   false claims across three document classes and the bucket did not move. That
   is a defect in the measure. **Do not fix it in a chat that benefits from the
   fix** — propose it, disclose the re-base, then apply it in the following chat.

4. **Documents disagreeing with each other.** *(medium)* The remaining untested
   direction. Both the D10 defect (chat-11) and the D09 defect (chat-12) were a
   document contradicting another document, not contradicting the code. Build a
   list of claims that two documents both make and check they match. **This is
   the one sweep class chat-12 did not attempt**, and the phase record says
   explicitly that a fourth sweep of the same kind would be finding what it went
   looking for.

5. **Real detector payload schema** *(medium — blocked on the Railroad)*.

6. **Apply the supply-chain tools** *(high — blocked)*. Needs a release host with
   index access and a GPG key under written custody. All three tools exist and are
   tested; none is applied.

7. **D07 §14.5 — governing law, seat and forum** *(counsel, not engineering)*.

4b. **The build-history document is three chats behind.** *(medium)* The close gate
   reports that `build-history-summary.js` has no Stage for chat-12, and its last
   stage is Stage 13, which is chat-9. **Chat-10, chat-11 and chat-12 are all
   absent from the docx** — the gate's note names only chat-12 because it compares
   against the current chat, not against every chat since the last stage. Adding
   three stages and rebuilding the docx (with the italics tokeniser fixed in
   chat-9) is a real piece of work and the obvious candidate for a full phase.
   **Do not assume the next stage number from this file — read the generator.**

**Do not open chat-13 by assuming there is code to write.** Items 1–3 are an owner
action, a product decision and a rubric decision. Item 4 is a sweep and is the only
one likely to produce a commit.

---

## Master % Tracker at chat-12's close

Basis and per-row scoring: `assets/master-tracker-rubric-2026-11-13.md`. Re-derived
at close from the files.

| Bucket | Weight | Chat-11 close | Chat-12 close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

**Re-derive at chat-13's open rather than quoting 78.4.** The rubric exists so this
stops happening. Note the caveat above: the docket bucket cannot distinguish a
document that exists from a document that is true, so zero movement here does not
mean nothing was wrong.

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
  checker. Fresh agent, told to *falsify*. **It earned its keep in chat-12** —
  nine defects in work with a green suite of 400 behind it, including one where
  the commit message asserted a fix the diff did not contain.
- **Never `git add -A`.** Stage named files; check with `--ignore-cr-at-eol`.
- **Never `git checkout -- <file>`.** Use `/tmp` or copy-and-restore.
- Extract and commit the transcript at close, raw `.jsonl` included, snapshot taken
  *after* the last exchange.

---

## Environment traps — updated

- **Use `tools/eol_edit.py` for every docket edit.** `--show-ending` first: the
  docket is mixed (D09 and B04 are LF/CRLF differently, and B04 is CRLF). Row-by-
  row single-line edits are more reliable than multi-line blocks.
- **A guard's neighbour line can trip it.** Chat-12's `_no_admin_purge_route`
  failed on the ledger's own comment explaining that `DROP TRIGGER` is possible.
  Strip comments and strings before any substring capability test.
- **A retraction can wrap across lines.** The D09 correction opens its quotation
  on one line and closes it on the next, so per-line quote counting reads a
  retraction as a claim. Count over the preceding text.
- **`python3 -I -X pycache_prefix=/tmp/<dir>`** for every run; `-I` alone discards
  `PYTHONPYCACHEPREFIX`. **The full suite takes ~4–5 minutes** — `timeout_ms`
  ≥ 500000, or it dies at 120s and leaves an `index.lock`.
- **`git commit` leaves stale locks on this mount** (`index.lock`, `HEAD.lock`,
  `objects/*/tmp_obj_*`) even when it succeeds. `rm -f .git/*.lock
  .git/objects/*/tmp_obj_*` after each commit.
- **B04's inventory test fails on any line-count change** to a listed module. It
  caught both chat-12 commits before the suite did — expect to update the row and
  the quoted total together, and check the total is the *sum* (chat-12 got this
  wrong by one and the sum test caught it).
- **`AXIOM_DB_PATH` before importing `backend.main`** — the import runs
  `store.init_db()` against the repo root.
- **The AxiomDynamics folder is not mounted at a fresh session's open.** Call
  `request_cowork_directory` with `C:\Users\RGV\AxiomDynamics` before anything else.
- A file in `project-logs/transcripts/raw/` cannot be overwritten in place; write
  fresh and `mv -f` over it.

---

## Transcript

Chat-12 extracted and committed at close: **104 turns (4 user)**, raw snapshot
2.4 MB at `project-logs/transcripts/raw/2026-11-13-chat-12-final.jsonl`, readable
extract at `project-logs/transcripts/2026-11-13-chat-12.md`. The four user turns
were verified as things the owner actually typed.

## Push state

`git log --oneline origin/main..HEAD` is the only answer that counts. At chat-12's
close the tracking ref equals `HEAD`, which suggests the chat-12 commits went up —
but the sandbox cannot reach GitHub (`git push` and `git fetch` both fail HTTP 403
from the proxy), so the ref is not proof of what the remote holds. Check the
commits page; push with `PUSH-TO-GITHUB.bat` if anything is waiting.
