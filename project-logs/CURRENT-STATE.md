# AxiomDynamics — Current State

**Last updated:** 2026-11-09 (chat-3, A2/D08 arithmetic pass committed)
**Repository:** `C:\Users\RGV\AxiomDynamics`
**Remote:** `github.com/kaanju19-lang/AxiomDynamics` (private)
**Top commit on `origin/main`:** `ee9800c` as last confirmed. **Five commits are
unpushed** as of chat-3: `3d773ac`, `36b43bd`, `d6f25ac`, `05b161d` (chat-2
transcript and handoff) and `ed78962` (chat-3 arithmetic pass). Run
`PUSH-TO-GITHUB.bat` in the repo root.

---

## What this project is

Physics-first predictive maintenance for freight rail. Six named physical models
— thermodynamics with per-axle rolling z-score, peer median/MAD comparison,
kinematics, acoustics (BPFO/BPFI/BSF/FTF), same-axle left/right differential, and
an executive ROI panel — instead of black-box ML or fixed alarm thresholds.

The Master Brief Docket is in `client-assets/MASTER-BRIEF-DOCKET/`: 36 documents
across A (commercial), B (technical), C (deployment) and D (contractual) series
plus F (forms).

## Build status

**37 documents on disk.** The docket index (D00) carries 37 ID rows; 34 are
marked `**Built**` in bold, and B02 (.md) and B03 (.html) carry plain "Built" with
a format qualifier. D00 Part IV is the authority on status, not this file.

Open docket items are tracked in **D00 Part IV** — that table is the authority,
not this file.

## The largest known gap

**There is no detector ingest path.** No endpoint accepts a Railroad payload.
Every demonstration signal is generated from the physics equations on synthetic
traces. This is disclosed in B01 §7 gap #5, B02 §2 and the B03 status block.

Every demonstration number demonstrates **the method**, not the Railroad's data.
The validation chain — schema, timestamp, plausibility — is designed and not built.

## Open items, in priority order

1. **Two A2/D08 model findings — need an owner decision.** The arithmetic pass of
   2026-11-09 found **no arithmetic errors** in either document (78 of 78 figures
   recompute correctly). It did find that two *claims* do not reproduce from the
   shipped model. Full detail in
   `assets/a2-d08-arithmetic-pass-2026-11-09.md`; run the check with
   `python3 -I assets/a2-d08-arithmetic-pass.py`.
   - **Finding 1.** A2 §3.2 and D08 §3 claim ~2.0x return at 500 axles rising to
     ~4.1x at 10,000. The shipped models give 1.77x/3.36x on the A2 cost basis or
     2.36x/4.99x on A1's. No parameter set in the repo reproduces both anchors.
     The monotonic claim holds on every basis; the two anchor values do not.
   - **Finding 2.** D08 §5–§6 modelled benefits ($6–8M pilot year, $14–20M
     four-year, $40–60M six-year) run 5x–14x above the $696,675 annual benefit A1
     computes at identical inputs. D08 §5 states A1 must never be bypassed.
     One of the two models governs and it has not been chosen.
2. **D07 §14.5 — governing law and venue.** An open counsel decision, correctly
   labelled as open as of chat-2 (previously a blank pointing at an Order field
   that does not exist). Must be closed by signed addendum before first execution.
3. **A1 workbook regeneration.** Deliberately not regenerated during the
   arithmetic pass, because doing so would bake both open findings into a new
   file before the model question is settled. The builder is now fixed (see
   below) and will regenerate on demand once findings 1 and 2 are decided.
4. **D09 §4.4 supply-chain gaps** — SBOM (Q1 2027), hash verification of
   dependency downloads (Q1 2027), GPG-signed releases (Q2 2027). All disclosed.
5. **Disposition ledger** — currently overwrites rather than appends. The
   evidentiary claim in F09 is ahead of the code until AD-3 lands (Q2 2027).

## A1 builder — fixed in chat-3

Two defects in `A1-ROI-MODEL/build_roi_calculator.py`, both cosmetic to the
workbook but both real if anyone runs it:

- The sheet-5 assumptions note attributed a **2% catastrophic escalation rate** to
  a model whose cell B17 has held **0.05%** since the correction. A reader
  reconciling the sheet against its own footnote would find a ten-fold conflict.
- The script saved to `/sessions/.../mnt/outputs/...`, a path inside the destroyed
  chat-1 sandbox, so running it raised `FileNotFoundError`. It now writes beside
  itself.


## Git state

The sandbox **cannot reach GitHub** — `git push` and `git fetch` both fail with
HTTP 403 from the proxy. Its `origin/main` ref therefore only advances when the
owner pushes and the sandbox is told the result. Do not trust it as evidence of
remote state without checking the commits page.

**Pushing is done by the owner**, with `PUSH-TO-GITHUB.bat` in the repo root. It
prints the commits waiting to go up and verifies afterwards.

**As of 2026-11-09, everything is pushed.** GitHub's top commit is `2ec168b`,
confirmed by the owner against the commits page.

**The host repo at `C:\Users\RGV\AxiomDynamics` is authoritative for push state.**
Verify by opening the commits page.

**The line-ending trap.** `git status` in this repo lists nearly every tracked file
as modified on a fresh Windows checkout. It is CRLF working-tree content against
LF blobs, not a content change — `git diff --ignore-cr-at-eol` returns empty.
There is no `.gitattributes` and `core.autocrlf` is unset. **Always check with
`--ignore-cr-at-eol` before believing a diff stat**, and never let an editor
rewrite a whole file's endings into a commit: doing so once during chat-3 turned a
two-line fix into 1,248 changed lines, which had to be reset and recommitted.


## What was lost in the chat-1 → chat-2 transition

Recorded here so nobody goes looking for it:

- Three commits built at the end of chat-1 (`0b66d21`, `cb4f74d`, and the
  F00/D07/Q6 work) existed only in the old sandbox. **`F00` Rule 7, the D07 §14
  rewrite and Q6 were rebuilt into the repository in chat-2.** The project-logs
  structure was rebuilt. The transcripts were not and cannot be — see
  `README.md`.
- Because the rebuild is a reconstruction rather than a recovery, the wording may
  differ from what chat-1 wrote. The *decisions* are identical; the prose is not
  guaranteed to be. Do not treat the current text as a restoration of an earlier
  draft.

## Standing instructions

- **[WORK LOCATION] All project work is written directly into this repository, first pass, and committed in the same pass.** No drafts in sandbox scratch space — that is how chat-1's final phase was lost.
- Keep the same concept throughout — consistency of framing across every document.
- Internal analysis goes in `assets/`, never `client-assets/`.
- Verify against the file before writing the claim.

## Why chat-1's work was lost — the mechanism

Not a deletion. The work was never on the owner's machine.

Chat-1 built the repo inside a temporary sandbox container. To get anything out
it bundled the repo, embedded the bundle in a `.bat`, and the owner ran it once —
which is how `de9b245` reached GitHub. **Everything chat-1 did after that push
stayed in the container**, including the F00 Rule 7 work, the D07 §14 rewrite, Q6
and the transcripts. The bundle was never remade. When the session ended the
container was destroyed and took all of it.

The failure was treating "committed" as "safe." Inside that container it only
meant "saved somewhere that is about to be emptied."

**The rule that follows:** there is no automatic export. A commit in the sandbox
is not durable until it is in `C:\Users\RGV\AxiomDynamics` and pushed. Never tell
the owner work is saved without saying where it physically is.
