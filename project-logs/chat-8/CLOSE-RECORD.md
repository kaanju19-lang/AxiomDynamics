# Chat-8 close — what was saved, and where

**When:** 2026-11-11. Return after the fact and this file answers "is everything
on disk?" without needing the transcript.

---

## The owner's instruction

> save all assets and raw chat transcripts to folder disk. see you in new chat-9

"Folder disk" is `C:\Users\RGV\AxiomDynamics` — the repository itself. Nothing
was left in a sandbox, a `/tmp` path or a temporary folder, because that is how
chat-1's conversation was destroyed.

## Conversation record

| Item | Path | Verified |
|---|---|---|
| Readable transcript | `project-logs/transcripts/2026-11-11-chat-8.md` | **242 turns — 4 user, 238 assistant**; every user turn read back and recognised |
| Raw session log | `project-logs/transcripts/raw/2026-11-11-chat-8-snapshot.jsonl` | **1,984 lines, all parse as JSONL**; exact prefix of the live log |
| Index | `project-logs/transcripts/README.md` | both rows added; the write trap recorded |

The extraction was done from a copy of the live log taken after the owner's
closing message, so every exchange in chat-8 is in it. The log keeps growing
while the session is open, so the snapshot is a **prefix** of the live file —
that is the correct and only honest state for a snapshot taken mid-session. The
close gate asserts the prefix relationship rather than a byte-equality that
could never hold.

## Handoff documents

| Item | Path |
|---|---|
| State of the project | `project-logs/CURRENT-STATE.md` (phase one and phase two sections) |
| Chat-8 carry-forward | `project-logs/chat-8/CARRY-FORWARD.md` — what closed, what the fixes were, the chat-9 ladder |
| Chat-8 narrative | `project-logs/chat-8/SUMMARY.md` |
| Phase-one account | `assets/mutation-survivors-closed-2026-11-11.md` |
| Phase-two account | `assets/key-custody-procedure-2026-11-11.md` |

The carry-forward contains **no commit hash**, only the command that answers the
question (`git log --oneline origin/main..HEAD`). A hash written into a file is
stale the moment the commit that contains it is made.

## Build assets

All code, tests and docket changes from chat-8 are committed: `backend/attribution.py`,
`backend/key_directory.py`, `tools/issue_reviewer_key.py`,
`tests/test_issue_reviewer_key.py`, and the test additions to
`test_attribution.py`, `test_key_directory.py`, `test_ingest.py`,
`test_ingest_auth.py` and `test_http_session.py`; the docket edits to B01, B02,
C01, C02, D00, D09 and F08; and the mutation driver at
`assets/mutation-ingest-auth.py`.

**Suite at close: 359 passed, 0 failed**, re-run by the close gate against a
freshly created output file.

---

## The close gate had to be repaired before it could be trusted

`project-logs/close-gate.sh` carried chat-7's hardcoded session mount and
transcript ids, so it could only ever pass in that one session. Four defects, all
fixed in this close:

1. **Hardcoded mount and session ids.** Now derived at runtime: the repo root
   from `BASH_SOURCE`, the session log as the newest `.jsonl` in the session
   directory, the snapshot as the newest committed one.
2. **A stale suite output file produced a false green.** The gate redirected the
   suite to a fixed `/tmp/suite.out`. That file existed, owned by another user,
   and was unwritable — so the redirect failed silently, `tail` read **chat-7's
   346**, and the gate printed `PASS suite green`. The real number was 359. It
   now writes to `mktemp`, checks the runner's exit status, and matches the
   summary line exactly.
3. **The same staleness made section 3 fail spuriously** (`14/15` modules). With
   a fresh file, all 15 are reached.
4. **The docx assertion pinned `Stage 11`**, which passes forever while the
   document silently ages. It now compares the docx against its own generator's
   top stage, and prints a loud note when the generator has no stage for the
   newest chat — currently the case, so **adding Stage 12 to
   `build-history-summary.js` and rebuilding the docx is item 1 of the chat-9
   ladder.**

That first false green is the sixth instance in this project of the same shape:
a green number that means less than it appears to. It was found by running the
gate and disbelieving its own output, not by reading it.
