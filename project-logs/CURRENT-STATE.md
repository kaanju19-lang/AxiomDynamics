# AxiomDynamics — Current State

**Last updated:** 2026-11-09 (chat-2)
**Repository:** `C:\Users\RGV\AxiomDynamics`
**Remote:** `github.com/kaanju19-lang/AxiomDynamics` (private)
**Top commit on `origin/main` as of chat-2 start:** `de9b245`

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

1. **A2 / D08 arithmetic pass.** Neither has been re-derived figure by figure
   since `cf2e6ba`. A wrong number in a rate card is found by a customer's AP
   clerk, not by us. **This is the highest-value remaining task.**
2. **D07 §14.5 — governing law and venue.** An open counsel decision, correctly
   labelled as open as of chat-2 (previously a blank pointing at an Order field
   that does not exist). Must be closed by signed addendum before first execution.
3. **D09 §4.4 supply-chain gaps** — SBOM (Q1 2027), hash verification of
   dependency downloads (Q1 2027), GPG-signed releases (Q2 2027). All disclosed.
4. **Disposition ledger** — currently overwrites rather than appends. The
   evidentiary claim in F09 is ahead of the code until AD-3 lands (Q2 2027).

## Git state, and a trap to avoid

The sandbox's `origin/main` ref is **stale** — it was set at clone time and never
updated. Running `git log origin/main..HEAD` *inside the sandbox* therefore
reports commits as unpushed that GitHub already has.

**The host repo at `C:\Users\RGV\AxiomDynamics` is authoritative for push state.**
Verify with `git fetch` from the host, or by opening the commits page.

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
