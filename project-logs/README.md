# AxiomDynamics — Project Logs

This folder is the memory of the project. It exists because the work outgrew a
single conversation, and a fresh thread with no record of what was decided
rebuilds the same mistakes.

## Structure

```
project-logs/
├── README.md               this file — structure, purpose, order of authority
├── CURRENT-STATE.md        authoritative project state, updated as work lands
├── chat-1/
│   ├── SUMMARY.md          what chat-1 did, decided, caught, and left open
│   └── CARRY-FORWARD.md    the handoff document for chat-2
├── chat-2/
│   └── SUMMARY.md          running record of chat-2
└── transcripts/            (see "A gap in the record", below)
```

## Order of authority

Three layers, and they are not equal:

1. **The repository itself** — `client-assets/MASTER-BRIEF-DOCKET/` and `assets/`.
   Where a document says one thing and a summary says another, the document wins.
2. **`CURRENT-STATE.md`** — what is built, what is pushed, what is open.
3. **`chat-N/SUMMARY.md`** — conclusions drawn from the above. Useful, never
   authoritative.

If any summary in this folder contradicts a document in the docket, **the docket
governs and the summary is corrected.**

## A gap in the record, stated plainly

Chat-1 produced readable transcripts of the three original conversations —
2,527 turns across `2026-11-08-847804b3.md`, `2026-11-08-d4e7e999.md` and
`2026-11-08-2c574bc2.md` — extracted from the raw session logs.

**Those files are gone.** They were written into a sandbox whose storage was
destroyed when that session ended, and the raw logs they were derived from went
with it. They never reached the GitHub repository. They cannot be recovered.

What survives is `chat-1/SUMMARY.md`, which is a distillation — a judgement about
what mattered, not the conversation. **Treat it as a summary and not as a
record**, which means: if a decision's origin matters and the summary does not
answer it, the summary cannot be made to. That information is not here.

The lesson that made this README exist is the same one, at a small scale: work
that exists only in one place is one failure away from not existing. From chat-2
forward, anything worth keeping is committed to the repository in the same pass
that produces it.

## Standing instructions

Two, from the original build, still in force:

- **"We will keep this same concept throughout."** The physics-first framing, the
  document structure, and the numbering discipline are not to be varied between
  documents. Consistency is the product.
- **"Strictly goes in our assets folder."** Internal analysis belongs in
  `assets/`, never in `client-assets/`. Client-facing material is
  `client-assets/MASTER-BRIEF-DOCKET/` only.

## The discipline that matters most

Chat-1's own summary records it, and the record confirms it: nearly every bad
citation in the project came from writing a claim from memory and checking
afterwards. The worst defect — the detector ingest path drawn as built when no
inbound route exists — came from the same habit applied to a diagram.

**So: verify against the file, then write. Not the reverse.**
