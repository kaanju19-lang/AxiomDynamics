# Chat-14 — Carry-Forward

**State at rollover:** suite **411 passed, 0 failed**. Nineteen test modules plus
the new one. The sandbox cannot reach GitHub; confirm the remote with
`git log --oneline origin/main..HEAD` and check the commits page. No hash is
written here, because a hash in a file is stale the moment it is committed.

**Chat-13 rolled over at the 125K cap with one ladder rung unbuilt.** That rung
is first in chat-14, and it is not optional.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `assets/chat-13-phase-record-2026-11-13.md` — the four defects, and the guard
   that could not fail
4. `assets/master-tracker-rubric-2026-11-13.md` — still the live rubric

---

## What chat-13 changed

| Commit subject | Effect |
|---|---|
| Close chat-12: phase record, carry-forward, state file, and the transcript | Five close artifacts chat-12 left **untracked**; a stale `.git/index.lock` cleared; stray `oo.txt` deleted |
| Cross-document sweep: three defects in two documents, and a guard that could not fail | B02 §2 contradicted its own §2 block; D09 §4.2 promised an Admin principal that does not exist and claimed role enforcement that does not exist; `tools/check_cross_refs.py` + 9 tests |

(Commit subjects are given rather than hashes; verify with `git log --oneline`.)

---

## The four things that matter most for chat-14

1. **A guard you wrote is not a guard you tested.** `check_cross_refs.py` was
   written, run, and returned clean. The mutation test showed it could not fail —
   `cited.startswith(h)` matched `14.7` against heading `1`. This is chat-12's
   lesson in the same chat that was carrying it forward. **Run the mutation every
   time, including on tools that already look right.**

2. **A test file that imports cleanly can contribute zero tests.**
   `tests/test_cross_refs.py` was first written as a `unittest.TestCase` class;
   `tests/run_tests.py` collects module-level `test_*` functions only. The suite
   printed 402, unchanged, and looked healthy. **Watch the number move when you
   add tests.** Module-level plain functions, not classes.

3. **The rubric's existence-versus-accuracy gap is now demonstrated over three
   chats.** Three false claims corrected, zero movement. Disclosed twice without
   being acted on. **Chat-14 proposes the re-base; chat-15 applies it.** Do not
   apply it in the chat that first scores better under it.

4. **Chat-12's close was claimed and not done.** The carry-forward said "working
   tree clean at close" and five artifacts were untracked. **Check
   `git status --porcelain -uall` at every chat's open**, not just `git log`.

---

## Next ladder — low to high, one at a time

1. **The independent adversarial audit of chat-13's work.** *(medium, but
   first — it is overdue, and the budget, not a judgement, is why it did not run)*
   Fresh agent, told to **falsify**. Target: the three document repairs, the
   rewritten `check_cross_refs.py`, and `test_cross_refs.py`. This project's
   audit has found nine defects in work with a green suite behind it twice
   running.

2. **The dashboard has never been seen.** *(low, owner action)* **Five chats.**
   `python3 -m backend.main`, then `http://127.0.0.1:8420/`. Also
   `frontend/render/panel.html`, committed 2026-11-13 with "not yet verified
   visually" in its own message. No renderer here; confirmed three times.

3. **The `gnupg` decision.** *(low to decide, blocks the asymmetric build)*
   `assets/asymmetric-signature-decision-2026-11-13.md` needs the owner to accept
   `gnupg` **and `dirmngr` — a daemon that performs network fetches** into an
   image whose proposition is zero outbound network. Cost objection removed by
   chat-12's benchmark. Commercial, not engineering.

4. **The remaining claim class.** *(medium)* Capability state for the three
   supply-chain controls — SBOM, hash pinning, release signing — across B01 §7,
   D09 §4.3/§4.4, D10 Part 5 and D00 Part VI. Three documents describe three
   tools in three states. The ingest and admin classes both produced defects;
   this is the next most likely pair.

5. **The rubric re-base.** *(low to propose)* See item 3 above.

6. **Real detector payload schema** *(medium — blocked on the Railroad)*.

7. **Apply the supply-chain tools** *(high — blocked)*. Release host with index
   access, GPG key under written custody.

8. **D07 §14.5 — governing law, seat and forum** *(counsel, not engineering)*.

---

## Master % Tracker at chat-13's close

Basis and per-row scoring: `assets/master-tracker-rubric-2026-11-13.md`.
Re-derived at close from the files.

| Bucket | Weight | Chat-12 close | Chat-13 close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

**Re-derive at chat-14's open rather than quoting 78.4.** Three chats of zero
movement against three chats of real document repair is the argument for the
re-base, and it is recorded in the phase record rather than acted on.

---

## Standing instructions, unchanged

- All project work written **directly into `C:\Users\RGV\AxiomDynamics`**, first
  pass, committed in the same pass. No drafts in the sandbox.
- **Verify against the file, then write.** Never cite from memory.
- **125K tokens per chat.** At the cap, alert and roll over.
- **Every build phase opens with a low→high priority ladder**, worked one item at
  a time.
- **Report the Master % Tracker at a phase's open and close**, derived from the
  written rubric.
- **Independent adversarial audit** when I author both the artifact and its
  checker.
- **Never `git add -A`.** Stage named files; check with `--ignore-cr-at-eol`.
- **Never `git checkout -- <file>`.** Use `/tmp` or copy-and-restore.
- Extract and commit the transcript at close, raw `.jsonl` included, snapshot
  taken *after* the last exchange.

---

## Environment traps — updated chat-13

- **`/tmp` root is not writable; `/tmp/<subdir>` is.** `mkdir -p /tmp/e13` first,
  then write the `eol_edit.py` old/new files there. A bare `/tmp/o1.txt` fails
  with Permission denied and the edit then reports "no match", which reads like a
  text-mismatch defect and is not one.
- **Use `tools/eol_edit.py` for every docket edit.** `--show-ending` first. B02
  and D09 are both **LF-only** (checked 2026-11-13, despite the handoff's claim
  that the docket is mixed; check per file rather than trusting either note).
- **`tests/run_tests.py` collects module-level `test_*` functions.** A
  `unittest.TestCase` class contributes zero tests and the suite still passes.
- **The full suite takes 4–5 minutes** — `timeout_ms` ≥ 580000.
- **B04's inventory test** checks `backend/` and `frontend/` only, so `tools/`
  and `tests/` additions do not move the quoted total. B04 currently reads
  **8,258**.
- **`git commit` leaves stale locks on this mount.** `rm -f .git/*.lock
  .git/objects/*/tmp_obj_*` after each commit.
- **`AXIOM_DB_PATH` before importing `backend.main`.**
- **The AxiomDynamics folder is not mounted at a fresh session's open.** Call
  `request_cowork_directory` with `C:\Users\RGV\AxiomDynamics` first.
- **A stale `.git/index.lock` needs `allow_cowork_file_delete` on the VM path**
  (`/sessions/<session>/mnt/AxiomDynamics/.git/index.lock`), then `rm`. Hit again
  at chat-13's open.
- **`python3 -I -X pycache_prefix=/tmp/<dir>`** for every run; `-I` alone
  discards `PYTHONPYCACHEPREFIX`.

---

## Transcript

Extracted at close. The raw snapshot in `project-logs/transcripts/raw/` and the
readable extract in `project-logs/transcripts/` carry the chat-13 filename date
`2026-11-13`.

## Push state

`git log --oneline origin/main..HEAD` is the only answer that counts. The sandbox
cannot reach GitHub (`git push` and `git fetch` both fail HTTP 403), so the local
tracking ref is not proof of what the remote holds. Push with
`PUSH-TO-GITHUB.bat` if anything is waiting.
