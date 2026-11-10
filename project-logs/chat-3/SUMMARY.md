# Chat-3 — Running Summary

Status: **in progress** as of 2026-11-09.
Opened with the chat-2 carry-forward. Its first act was to verify the inherited
state against the repository rather than trust the handoff, per the standing rule.

## Verification of inherited state (start of chat-3)

Read `CURRENT-STATE.md`, `chat-2/SUMMARY.md` and `project-logs/README.md`, then
checked the repo directly. Four things did not match the written record:

1. **Push state was stale in the carry-forward.** It named `785f335` and
   `ee9800c` as unpushed; both were already in `origin/main`, with `ee9800c` as
   the remote top. What was actually unpushed was the later transcript and
   handoff work — `3d773ac`, `36b43bd`, `d6f25ac`, `05b161d`.
2. **`chat-2/SUMMARY.md` still read "in progress"** and still claimed "Neither is
   pushed" about `f58b07c`/`c9b32bd`. Finalized and corrected.
3. **57 "modified" files were a line-ending artifact.** CRLF working tree against
   LF blobs; `--ignore-cr-at-eol` returned empty. Not content. Recorded in
   `CURRENT-STATE.md` so the next session does not re-investigate it.
4. Everything else was intact: 37 docket documents, `assets/`, and the chat-2
   transcript with three raw `.jsonl` files (5.8 MB).

## Work done in chat-3

### A2 / D08 arithmetic pass — complete

The highest-value item from both the carry-forward and `CURRENT-STATE.md`, and
untouched since `cf2e6ba`.

Built `assets/a2-d08-arithmetic-pass.py`: it recomputes every figure in A2 and D08
from its stated source equation and compares it to the document, exiting non-zero
on any mismatch. **78 of 78 computed figures agree.** No arithmetic error exists
in either document — every band total, worked example, site-fee product, payment
split, conversion credit, three-year row, performance cap, cumulative schedule and
the 5% escalation is correct as written.

Two *claims* did not reproduce. Both are model divergences rather than arithmetic
errors, and both are left open because fixing them means choosing which model
governs — an owner decision, not an editorial one:

- **Finding 1.** A2 §3.2 and D08 §3 claim ~2.0x at 500 axles rising to ~4.1x at
  10,000. The shipped models produce 1.77x/3.36x on the A2 cost basis, or
  2.36x/4.99x on A1's. No parameter set in the repository reproduces both anchors.
  The monotonic claim is true on every basis tested.
- **Finding 2.** D08 §5–§6 modelled benefits run 5x–14x above the $696,675 annual
  benefit A1 computes at identical inputs. D08 §5 states A1 must never be
  bypassed.

Full working, tables and recommended dispositions:
`assets/a2-d08-arithmetic-pass-2026-11-09.md`.

### A1 builder — two defects fixed

- The sheet-5 assumptions note attributed a **2%** catastrophic escalation rate to
  a model whose cell B17 has held **0.05%** since the correction. Corrected to
  name 0.05% and cite B17.
- The script saved to `/sessions/.../mnt/outputs/...`, a path inside the destroyed
  chat-1 sandbox, so running it raised `FileNotFoundError`. It now writes beside
  itself via `os.path.dirname(os.path.abspath(__file__))`.

The committed workbook was **not** regenerated: doing so would bake both open
findings into a new file before the model question is settled.

### Project logs corrected

`CURRENT-STATE.md` updated (push state, open items, the line-ending trap, the A1
builder fixes). `chat-2/SUMMARY.md` finalized and its push claims corrected.
`chat-2/CARRY-FORWARD.md` push numbers and "work waiting" section corrected.
`project-logs/README.md` tree now lists `chat-2/CARRY-FORWARD.md`, `chat-3/` and
`transcripts/raw/`.

## Verification performed

- Arithmetic: 78 figures computed independently in `assets/a2-d08-arithmetic-pass.py`,
  all matching. Script re-run from the committed tree and exits 0.
- Every A1 figure cited in the pass record was read from the built workbook
  (`openpyxl`, `data_only=True`), not from the builder source — the two differ on
  the pilot cost line.
- A2 and D08 confirmed untouched: `git diff --ignore-cr-at-eol` on both returned
  empty after the pass.
- Commit inspected for line-ending churn. The first attempt rewrote the builder to
  CRLF and produced 1,248 changed lines for a 2-line fix; reset and recommitted so
  the commit shows 420 insertions and 2 deletions.

## The build history document

Requested by the owner because chat-1's conversation no longer exists and the
build needed a readable record of itself. Produced as
`project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx` — 29 pages,
eight parts plus an appendix — with its generator committed beside it at
`project-logs/build-history-summary.js` so it can be rebuilt after a change.

Contents, in order: what the product is and why physics rather than ML; the six
models; the eight build stages across all 37 commits with every correction; the
38-artifact docket document by document plus the D00 Part IV precedence ladder;
the loss of chat-1's work, its mechanism and its cost; what chat-2 rebuilt and
how it verified it; internal strategy in `assets/`; the open items including both
chat-3 modelling findings; how to resume; and an appendix with the repository
map, the full commit chronology and a status table.

Written from the repository, not from recollection. Layout verified by rendering
to PDF and reading the pages: 29 pages, no overflow, tables within margins,
numbering restarting per list. Two defects were found and fixed in that pass —
all numbered lists shared one continuous sequence (Part VIII opened at "10."),
and the Word TOC field rendered empty in a converter that does not update
fields, so a static Parts table now carries the navigation.

## Commits

`ed78962` — the arithmetic pass, check script, pass record and builder fixes.
`a3ba43f` — the build history document and its generator.
`b3dcda4` — `CURRENT-STATE.md`: points at the summary, corrects the artifact
count, and replaces the hardcoded unpushed-hash list with an instruction to check
`git log origin/main..HEAD`.

**Push required.** Run `PUSH-TO-GITHUB.bat` in the repo root, then confirm with
`git log --oneline origin/main..HEAD` rather than trusting any hash written here.

## Next

1. Decide Finding 1 — strike or restate the 2.0x/4.1x anchors.
2. Decide Finding 2 — which model governs, A1 or D08 §5–§6.
3. Then regenerate the A1 workbook and re-run the check script.
4. D07 §14.5 governing law and venue remains open, unchanged by this pass.
