# AxiomDynamics — Project Logs

This folder is the memory of the project. It exists because the work outgrew a
single conversation, and a fresh thread with no record of what was decided
rebuilds the same mistakes.

## Structure

```
project-logs/
├── README.md               this file — structure, purpose, order of authority
├── CURRENT-STATE.md        authoritative project state, updated as work lands
├── AxiomDynamics-Build-History-and-Working-Summary.docx
│                           the long-form account of the whole build (34 pp)
├── build-history-summary.js  generator for the above; re-run after a change
├── extract_transcript.py   turns a raw session .jsonl into the readable extract
├── chat-1/
│   ├── SUMMARY.md          what chat-1 did, decided, caught, and left open
│   └── CARRY-FORWARD.md    the handoff document for chat-2
├── chat-2/
│   ├── SUMMARY.md          what chat-2 did; closed 2026-11-09
│   └── CARRY-FORWARD.md    the handoff document for chat-3
├── chat-3/
│   └── SUMMARY.md          chat-3, closed 2026-11-10
├── chat-4/
│   ├── SUMMARY.md          chat-4, closed 2026-11-10
│   └── CARRY-FORWARD.md    the handoff document for chat-4
├── chat-5/
│   └── CARRY-FORWARD.md    the handoff document for chat-5
└── transcripts/            chat-2 onward, readable + raw jsonl (chat-1 is lost)
    ├── 2026-11-09-chat-2.md   readable extract
    ├── 2026-11-09-chat-3.md   readable extract
    ├── 2026-11-10-chat-4.md   readable extract
    └── raw/                the source logs, committed with each transcript
```

**Start with the build history if you are new to this project.** It is 34 pages
covering the product, every build stage and its corrections, the full docket, the
loss of chat-1's work, the internal strategy, and the open items — written to be
read cold, without the conversation it describes. Revised 2026-11-10 at chat-4's
close to carry Stage 8, the model decision, and the closure of both findings.

## Order of authority

Three layers, and they are not equal:

1. **The repository itself** — `client-assets/MASTER-BRIEF-DOCKET/` and `assets/`.
   Where a document says one thing and a summary says another, the document wins.
2. **`CURRENT-STATE.md`** — what is built, what is pushed, what is open.
3. **`chat-N/SUMMARY.md`** — conclusions drawn from the above. Useful, never
   authoritative.

If any summary in this folder contradicts a document in the docket, **the docket
governs and the summary is corrected.**

## The record, and the gap in it

`transcripts/` holds the conversation logs. **`2026-11-09-chat-2.md`,
`2026-11-09-chat-3.md`, `2026-11-10-chat-4.md` and their raw `.jsonl` files are
here** — each session is extracted and committed at its close, raw log included,
and that is the rule for every session.

**Chat-1 is lost.** It covered 2,527 turns across three raw session logs from
2026-11-08 04:24 to 2026-11-10 03:00. Chat-1 extracted readable transcripts from
them — `2026-11-08-847804b3.md`, `2026-11-08-d4e7e999.md`, `2026-11-08-2c574bc2.md`
— but wrote them into a sandbox whose storage was destroyed when the session
ended. They never reached this repository, and the raw logs went with them.

There is no copy anywhere. What survives is `chat-1/SUMMARY.md`, which is a
distillation — a judgement about what mattered, not the conversation.

**The lesson, stated where it will be read:** work that exists in one volatile
place is one failure away from not existing. From chat-2 forward every session is
extracted and committed in the same pass that produces the work, and the raw log
is committed with it.

## Standing instructions

Two, from the original build, still in force:

- **"We will keep this same concept throughout."** The physics-first framing, the
  document structure, and the numbering discipline are not to be varied between
  documents. Consistency is the product.
- **"Strictly goes in our assets folder."** Internal analysis belongs in
  `assets/`, never in `client-assets/`. Client-facing material is
  `client-assets/MASTER-BRIEF-DOCKET/` only.

A third, added 2026-11-09 after the loss described above:

- **"Drop all the entire project work directly in AxiomDynamics folder so we don't
  lose any data from sandbox."** Work is written into this repository on the first
  pass and committed in the same pass that produces it. No drafts parked anywhere
  else. The sandbox is scratch space and its storage does not survive a session;
  this repository does.

## The discipline that matters most

Chat-1's own summary records it, and the record confirms it: nearly every bad
citation in the project came from writing a claim from memory and checking
afterwards. The worst defect — the detector ingest path drawn as built when no
inbound route exists — came from the same habit applied to a diagram.

**So: verify against the file, then write. Not the reverse.**
