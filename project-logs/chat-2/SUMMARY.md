# Chat-2 — Running Summary

Status: **closed 2026-11-09.** Finalized at the start of chat-3, which found this
file still marked "in progress" and still carrying push claims that had gone stale.
Where this file disagrees with `CURRENT-STATE.md` or the docket, those win.

## How chat-2 started

Chat-2 opened on 2026-11-09 as a fresh thread. Its first act was to verify it knew
what chat-1 was about, rather than assuming it.

## State inherited from chat-1

The authoritative project state is `project-logs/CURRENT-STATE.md`. Read that
before this file. Where anything in this summary disagrees with `CURRENT-STATE.md`
or with the transcripts under `project-logs/transcripts/`, they win.

## What chat-2 has done so far

1. **Verified the inherited state** rather than trusting the handoff. Found that
   none of chat-1's final work was in the repository: `F00` still read "six
   rules", `D07 §14.3` still pointed at a non-existent Order field,
   `assets/legal-architecture/` was empty, and `project-logs/` did not exist.
   The old sandbox and its raw logs were gone, so recovery was impossible.
2. **Rebuilt F00 Rule 7** — a fill-in blank and an unmade decision are now
   different things, written differently. Rule 4 amended so brackets mean
   definitions only. D00's rule count corrected from five to seven.
3. **Rebuilt D07 §14** — §14.3 now defers to an explicit §14.5 that states
   governing law and seat as an open counsel decision, with (a) what must be
   decided, (b) who decides and by when, (c) the Texas default stated as an
   expectation and not a term, (d) a defined fallback if an Order is executed
   while it is open. D03 points at §14.5 rather than holding a second blank.
4. **Rebuilt Q6** in `assets/legal-architecture/` — Texas LLC, Delaware declined
   on reasons specific to this company, the personal guarantee identified as the
   real threat to the shield, and the support boundary as a substitution table of
   sentences an engineer can say at 17:55. All formation figures re-verified
   against official sources; the Delaware annual tax left explicitly unresolved
   because sources still conflict ($300 vs $400 for 2026).
5. **Closed the D09 signed-release gap** — signing previously appeared only as a
   §4.4 row. Added §7.3 stating plainly that artefacts are unsigned today, what
   the SHA-256 manifest does and does not prove, and what changes at Q2 2027.
6. **Rebuilt project-logs** with the transcript loss documented rather than
   papered over.

## Verification performed

- Citational: every D-reference in Q6 and every §-reference in the rebuilt
  sections resolved to a real heading. Two errors found this way and corrected —
  `D06 §2.4` → `§7.4` and `D03 §12` → `§9`.
- Count consistency: no document still says "six rules" or "five documentation
  rules"; D00 gap table now cites D09 §7.2 and §7.3.
- Duplicate-heading scan across all 36 docket documents: clean (D04's repeats are
  its five SOW templates).
- Scope: Q6 confirmed absent from `client-assets/`.
- Diff inspected with `--ignore-cr-at-eol`: 536 real insertions against 7 real
  deletions. The larger raw numbers are CRLF conversion from the Windows
  checkout, not content.

## Commits

`f58b07c` — the rebuild. `c9b32bd` — push helper. Both were superseded later in
the session by `785f335` and `ee9800c`, then by the transcript and handoff commits.

**Correction made in chat-3:** when this summary was written it said "Neither is
pushed." By close of chat-2 all six commits were in place locally and the owner
had pushed through `ee9800c`, which became the top of `origin/main`. Four commits
were still unpushed at the chat-2 → chat-3 boundary — the transcript and handoff
work (`3d773ac`, `36b43bd`, `d6f25ac`, `05b161d`) — because they were made after
that push. See `CURRENT-STATE.md` for authoritative push state.


## Next

The A2/D08 arithmetic pass — the highest-value remaining task, and untouched
since `cf2e6ba`. **Completed in chat-3:** 78 of 78 figures recompute correctly; no
arithmetic error found. Two model-level findings were raised and left open for a
decision. See `assets/a2-d08-arithmetic-pass-2026-11-09.md`.


## Carried over from chat-1 — must not be lost

1. **Three sandbox commits never reached GitHub.** `de9b245` is the top commit
   on `origin/main`. Everything chat-1 built after it — `0b66d21` (project-logs
   structure), `cb4f74d` (transcripts), the F00 Rule 7 fix, the D07 §14 rewrite,
   and Q6 — exists only in the old sandbox. Verified: `F00` still says "six rules",
   `D07 §14.3` still points at a non-existent Order field, and
   `assets/legal-architecture/` is empty.
2. **The recommendation was already recorded in chat-1's own transcript:** the
   SBOM and signed-release language in D09 is listed as a gap in §4.4 while §4.3
   still reads as a commitment. It needs one pass to make every section tell the
   same story.
3. **The arithmetic pass** — A2 and D08 re-derived figure by figure, not yet done
   since `cf2e6ba`.

## Next action at the time of writing

Rebuild the lost chat-1 work into the real repository, in one verified pass, and
push it.
