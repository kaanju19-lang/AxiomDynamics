# Transcripts

Conversation records for the project.

## What is here

| File | Turns | Covers |
|---|---|---|
| `2026-11-09-chat-2.md` | 256 | chat-2, from the first line to the point of extraction |
| `raw/2026-11-09-chat-2.jsonl` | 780 events | the unprocessed session log, 1.6 MB |

The `.md` is the readable version: every user and assistant turn in order. Tool
calls are recorded inline so you can see what was run; tool *output* — command
results, file listings, screenshots — is omitted, because it is bulk without
being conversation.

The `.jsonl` in `raw/` is the source. Don't edit it. It is what the `.md` was
derived from, so if the extraction ever looks wrong, the raw file is the answer.

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
extracted and committed at the end of the session it belongs to, raw log included.
Nothing is left in sandbox storage to be lost.

## Reproducing an extraction

The raw log lives at
`.claude/projects/session/<session-id>.jsonl` inside the session's mounted
folder. The extractor keeps only `user` and `assistant` events, drops sidechains
and system reminders, and writes them in order. It is a small script and easy to
rewrite if needed; the point is that the **raw file is committed**, so the
conversation survives even if the extractor does not.
