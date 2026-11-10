# AxiomDynamics — Current State

**Last updated:** 2026-11-09 (chat-2, all work pushed)
**Repository:** `C:\Users\RGV\AxiomDynamics`
**Remote:** `github.com/kaanju19-lang/AxiomDynamics` (private)
**Top commit on `origin/main`:** `2ec168b` — confirmed on GitHub 2026-11-09. Everything is pushed; nothing is outstanding.

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
