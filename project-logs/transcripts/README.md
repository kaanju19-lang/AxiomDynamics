# Transcripts

Conversation records for the project.

## What is here

| File | Turns | Covers |
|---|---|---|
| `2026-11-09-chat-2.md` | 256 | chat-2, from the first line to the point of extraction |
| `2026-11-09-chat-3.md` | 582 | chat-3, from the first line to the transcript phase |
| `raw/2026-11-09-chat-2.jsonl` | 780 events | the unprocessed chat-2 log, 1.6 MB |
| `raw/chat-2-final.jsonl`, `raw/chat-2-close.jsonl` | — | later snapshots of the same chat-2 session |
| `raw/2026-11-09-chat-3-snapshot.jsonl` | 3,385 events | the chat-3 log, 13.2 MB, valid JSONL |

The `.md` is the readable version: every user and assistant turn in order. Tool
calls are recorded inline so you can see what was run; tool *output* — command
results, file listings, screenshots — is omitted, because it is bulk without
being conversation.

The `.jsonl` in `raw/` is the source. Don't edit it. It is what the `.md` was
derived from, so if the extraction ever looks wrong, the raw file is the answer.
Commit both: an extract alone is a summary pretending to be a record.

**Chat-3's raw log is a mid-session snapshot.** It captures the session as of the
moment the transcript was taken, not the final state, because the session was
still running. Later work in that session is covered by `chat-3/SUMMARY.md`, and
the raw log can be re-snapshotted at close.

## What is NOT here, and cannot be

**Chat-1 — the original build conversation — is lost.**

It ran from 2026-11-08 04:24 to 2026-11-10 03:00 and covered 2,527 turns across
three raw session logs. Chat-1 did extract those into readable transcripts. They
were written into a sandbox whose storage was destroyed when the session ended,
and they never reached this repository. The raw logs they came from were in the
same place and went with them.

There is no copy. No archive, no mirror, no cache. `project-logs/chat-1/SUMMARY.md`
is the only surviving record of that conversation, and it is a distillation — a
judgement about what mattered, not the conversation itself.

**This is why it will not happen again:** every session from chat-2 forward is
extracted and committed in the same pass that produces its work, raw log included.
Nothing is left in temporary storage to be lost.

## Reproducing an extraction

The raw log lives at
`.claude/projects/session/<session-id>.jsonl` inside the session's mounted
folder. The extractor keeps only `user` and `assistant` events, drops sidechains
and system reminders, and writes them in order.

Three things it must do, learned the hard way on chat-3:

1. **De-duplicate before writing anything.** The log appends each assistant
   message several times while it streams. Without de-duplication by
   `message["id"]` and by tool-call block `id`, every paragraph and every tool
   call appears three or four times. The first chat-3 extract was 1,062 turns and
   contained duplicates; the correct count is 582.
2. **Drop machine-injected `user` messages.** Skill bodies (they begin
   `Base directory for this skill:`), compaction summaries (they begin `This
   session is being continued from a previous conversation`) and slash-command
   wrappers arrive with `role: user` but were not typed by anyone. Leaving them in
   makes the transcript unreadable and misrepresents what the user said.
3. **Verify the user turns against what you remember.** The extract is only
   trustworthy if you can read the user's actual messages back and recognise
   every one. If a message is missing or a prompt appears that nobody typed, the
   filter is wrong.

The extractor is a small script and easy to rewrite if needed; the point is that
the **raw file is committed**, so the conversation survives even if the extractor
does not.
