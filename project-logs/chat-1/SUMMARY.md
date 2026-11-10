# Chat-1 — Summary

**Thread:** the original AxiomDynamics build conversation, resumed across three
raw session logs.
**Span:** 2026-11-08 04:24 → 2026-11-10 03:00 (per the transcript index produced
at the end of chat-1).

> **What this file is.** A distillation, written at the close of chat-1. The
> conversation itself — 2,527 turns — was extracted into readable transcripts and
> **those files were lost** when the sandbox was destroyed (see
> `../README.md`). This summary is therefore the only surviving record of chat-1,
> and it is a judgement about what mattered, not a transcript. Read it knowing
> that.

---

## What chat-1 built

The project began from a Master Build & Rollout prompt that set the physics-first
philosophy: named physical models, rolling per-axle z-scores, kinematics from
`E_k = ½mv²`, acoustics against the standard bearing defect-frequency equations —
explicitly *not* black-box ML and *not* fixed absolute alarm thresholds. That
philosophy was never varied, at the user's standing instruction: **"we will keep
this same concept throughout."**

From there, chat-1 built the Master Brief Docket: the A-series commercial
documents (ROI model, rate card), B-series technical (blueprint, flow map,
infographic, stack disclosure, data residency), C-series deployment (self-deploy
SOP, certification), D-series contractual (D01–D14), and the F-series forms
(F00–F13).

Commits that reached GitHub, in order: `d05501f` (D14), `e8a08fc` (D13),
`7c47aa6` (D12/D11/D02), `96e058c` (D07/C01/C02), `b9aa4a8` (D05/D06/D09, 12
loopholes closed, 16/30 built), `cf2e6ba` (Q7: F00–F13, A2, D03, D04, D01, D10,
two-pass consistency audit), `33ccc7e` (B02/B03, build status reconciled),
`de9b245` (B02/B03 corrected to disclose no detector ingest path).

## What chat-1 caught

The corrections matter more than the builds, because they are the pattern chat-2
inherits:

- **The detector ingest path was drawn as built.** B02 and B03 showed a flow from
  detector to edge inference; no endpoint accepts a Railroad payload. Corrected in
  `de9b245`. This is the largest gap in the docket and it was found by checking a
  diagram against the code, not by reading the diagram.
- **D09 §4.3 promised an SBOM that §4.4 listed as a gap** — in the same document,
  six lines apart. Corrected to state the negative plainly.
- **D07 §15.4 contradicted D03 §12.1** on convenience termination. Both cannot be
  right; the position was made consistent.
- **D08 is a commercial annex, not an instrument to sign.** Relabelled so nobody
  executes it.

## What chat-1 decided

- **A2 governs price across the entire docket.** Where any other document's fee
  differs from A2, A2 wins.
- **D07 and D02 are what a customer executes.** D08 explains the money; it is not
  a contract.
- **Texas law is the working expectation** for venue — recorded as an expectation,
  not a term.
- **The document precedence order in D00 Part IV governs** conflicts between
  documents.

## What chat-1 left open

1. **The A2/D08 arithmetic pass** — not re-derived since `cf2e6ba`.
2. **D07 §14.3 venue** — pointed at an Order signature-block field that no Order
   template contains. (Found at the very end of chat-1; rebuilt in chat-2.)
3. **D09 signed-release language** — existed only as a §4.4 gap row, never stated
   affirmatively. (Closed in chat-2 as §7.3.)
4. **The F00 blank-versus-decision distinction** — a blank and an unmade decision
   were written identically. (Closed in chat-2 as Rule 7.)
5. **Q6 — entity formation and support boundary.** Written at the close of
   chat-1, lost with the sandbox, rebuilt in chat-2.

## The pattern worth carrying forward

Nearly every bad citation in chat-1 came from writing a claim from memory and
checking it afterwards. The worst defect in the project came from the same habit
applied to a diagram: it looked right, so nobody checked whether it was true.

**Verify against the file, then write.**
