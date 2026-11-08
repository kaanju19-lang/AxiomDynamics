# Library Reconciliation — Air-Gapped Governance Reference vs. Master Brief Docket

**Internal working document.** Not client-facing. Analysis of the 47-document `Railroad_AirGapped_Governance_Master_Library` against our `client-assets/MASTER-BRIEF-DOCKET`.

**Date:** 2026-11-08

---

## 0. What the reference library actually is

47 markdown files, ~2,435 lines, ~1,380 substantive lines after stripping tables and checkboxes. **Every document is an unpopulated template.**

Verified by grep across the whole collection:

| Sought | Hits |
|---|---|
| escrow | **0** |
| insurance | **0** |
| indemn | **0** |
| liab (liability) | **0** |
| testament / attestation | **0** |

So the collection contains **no legal substance whatsoever**. It is a process scaffold: registers, matrices, gates, sign-off tables. Valuable as a *shape*; empty as *content*.

## 1. The library's most serious defect — do not import this

Five documents **assert outcomes that have not occurred**:

- `Executive_Readiness_Dashboard.md` — every domain "Green, 100%"
- `Executive_Summary_Binder.md` — every domain "Complete"
- `Governance_Library_Validation_Report.md` — "Readiness: 100%. Pending Items: 0"
- `Final_Program_Closure_Report.md` — "Program Status: CLOSED"
- `Benefits_Realization_Report.md` — "Benefits Realization Status: ACHIEVED"

These are pre-filled success claims inside documents whose stated purpose is **auditable evidence**. An auditor who opens the Executive Readiness Dashboard and sees 100% green before a single test has run will not conclude the programme is ready. They will conclude the entire evidence set is fabricated, and they will be right to.

This is the exact failure our Docket Index Part IV rule 6 exists to prevent — a document claiming something the system does not do. **If we adopt these documents we must strip every pre-filled status and leave them genuinely empty until evidence exists.** Adopting the shape is right; adopting the filled-in claims would be self-inflicted.

## 2. What this library has that we do not — the real gaps

Ranked by whether the absence would **block a deal**.

### Tier 1 — blocking

**G1. Evidence discipline. No equivalent anywhere in our docket.**
Master Evidence Register (MER) and Master Hash Manifest Registry (MHMR). Every artifact gets an ID, timestamp, operator, SHA-256, validation result, approval.

Why this blocks: our entire differentiation is an auditable record of human review. We assert an append-only disposition ledger as our regulatory artifact. **We have no mechanism to prove any assertion we make about our own delivery.** A railroad security reviewer will ask "show me the hash manifest for the release" and we have nothing to show. B04 §7 already admits we produce no SBOM and sign no artifacts.

The irony is sharp and worth stating: we sell evidentiary integrity, and we ship no evidence.

**G2. Air-gap media transfer procedure.**
Air-Gap Transfer Manifest, Media Control Register, Chain of Custody Register, NIST SP 800-88 sanitisation.

Why this blocks: we chose AD-1, fully on-premise zero-egress. That choice has a direct consequence we documented as a *cost* in B01 §8 but never operationalised: **every update, patch and data transfer must physically cross the gap on removable media.** We have no procedure for that at all. No manifest, no dual-person verification, no serial tracking, no sanitisation record. This is not a nice-to-have — it is the operating reality of the architecture we committed to.

**G3. Authorization gate. No ATO-equivalent.**
Authority To Operate, Operational Readiness Review, Deployment Go/No-Go.

Why this blocks: our D02 Master Pilot Agreement could currently execute with **nothing having verified the system is fit to run.** A Class I railroad will not accept a system into an operational environment without an authorisation decision with named signatures. We have a pilot agreement and no gate in front of it. This is the single largest structural hole in our docket.

**G4. Disaster recovery with stated RTO/RPO.**
Disaster Recovery Runbook, Recovery Test Procedures, Recovery Test Report.

Why this blocks: a system feeding safety decisions with no stated recovery objective is not deployable. If the edge box dies, how long until advisories resume, and what is lost? We cannot answer. For a safety-adjacent system this is asked in the first review, not the last.

### Tier 2 — significant

**G5. Change control and configuration baselines (CMDB).** We have D06 support governance but no configuration management. If we patch their box, what baseline did we change from?

**G6. Rollback and deployment exercise.** The library rehearses deployment and proves rollback. We have no rollback plan. If a release fails on their box, we improvise.

**G7. Records retention schedule.** Our D09 says retention is "TBD." The library gives a concrete structure (7 years governance/security/audit/validation/incident, 5 years change records). Regulatory evidence retention is usually multi-year — this needs to be settled, not deferred.

**G8. Continuous compliance monitoring.** Post-deployment control surveillance. We have nothing after installation.

**G9. Competency verification for certification.** Our C02 defines roles but no assessment method. The library's "Competency Verification: role / assessment / score / accepted" is the missing piece — and directly strengthens the Canadian regulatory argument.

**G10. RACI matrix.** No defined split of responsibility between us and the Railroad. Inevitable source of dispute without one.

**G11. Governance lifecycle map (10 stages).** Strategy → Architecture → Build → Validation → Accreditation → ORR → ATO → Operations → Ownership Transfer → Closure → Archive. A genuinely good backbone. Our docket is a document *list*; this is a *sequence with exit criteria*.

## 3. The structural conflict — the finding that matters most

**The library assumes a model we do not have, and cannot adopt without destroying our commercial position.**

Its `18_CLIENT_OWNERSHIP` section requires transfer of: **source code, AI models, embeddings, tokenizers, prompts, knowledge graph, infrastructure definitions (Terraform/Ansible/Kubernetes), hardening baselines** — everything, to the client, at handover.

Our D07/D08 position is the opposite: AxiomDynamics retains IP and licenses it; the client gets a licence, its own data, and source-code **escrow triggered only on insolvency**.

These cannot both be true, and the choice is not a wording exercise:

- **If we hand over source code, we have sold one bespoke integration.** The price is a services engagement, and we cannot license the same build to the next railroad. Our valuation collapses to a project fee.
- **If we retain IP, we are a product company.** Repeatable licensing, which is what the entire D08 model — axle bands, per-site fees, performance component — is built to price.

The library is shaped for a *systems integrator delivering a bespoke build and closing the programme out*. We are shaped for a *product licensed repeatedly across carriers*. Its final lifecycle stages — "Ownership Transfer," "Program Closure," "Archive" — do not fit a product licence at all. A product is not closed out and archived; it is versioned and supported.

**Recommendation: adopt the library's evidence, integrity, authorisation and recovery spine. Reject its ownership-and-closure spine.** Keep the escrow position. Separate the concepts explicitly: *asset documentation* is transferable (they get drawings, runbooks, baselines); *source and model rights* are not, absent an insolvency trigger.

This decision should be recorded before C01 and the D-series legal drafts get written, because it changes their substance.

## 4. What is irrelevant — skip without concern

**The AI/ML assumptions.** `06_AI`, `07_KNOWLEDGE_GRAPH`, and large parts of `04` and `18` assume a learned system: training data manifests, feature lists, hyperparameters, embeddings, tokenizers, prompts, graph ontologies, inference weights.

**AxiomDynamics is deterministic and non-LLM.** Importing "Prompt Governance" or "Embedding Lineage" into a physics platform's governance pack would actively damage us — a technical buyer reading it concludes we do not understand what we built. Reject outright.

*One nuance worth keeping:* "model validation" is still required, just in a different sense. A deterministic bearing-defect equation still needs **verification and validation** — do the equations derive from accepted tribology, are the constants sourced, does the output match known failed-bearing cases? That is *physics V&V*, not ML validation. Keep the requirement, reject the framing.

**Enterprise infrastructure assumptions.** Kubernetes, hypervisors, VM templates, NAS/SAN, VLAN inventories, Terraform, Ansible. Our architecture is one container on one box. Skip. (If a railroad insists on k8s, that becomes a question, not an assumption.)

**The compliance frameworks — premature, not irrelevant.** NIST 800-53, 800-82, IEC 62443, ISO 27001. A Class I security review *will* ask which standard we map to, and **IEC 62443 is genuinely apt** for OT-adjacent industrial deployment. But asserting compliance we have not assessed is the fabrication problem again. Adopt the *mapping concept*; mark current status honestly as "not assessed."

**Consulting artefacts.** Benefits Realization, Stabilization Metrics, Programme Closure, Archive Index. Programme-management output for a services engagement. Not our model. Low priority at best.

## 5. What we have that the library lacks — do not lose it

The comparison cuts both ways. The library has **no commercial, legal or domain substance**:

- No pricing, licensing, ROI model
- No indemnity, liability, insurance, or escrow (zero hits, verified)
- No IP ownership *terms* — it lists assets, not rights
- No limitation of liability, no safety-critical disclaimer
- No regulatory status statement (FRA / Transport Canada / ARTF)
- No data processing agreement, no NDA
- No pilot agreement or statement of work
- No carrier intelligence

**The library is a skeleton of assurance process. Our docket is the substance of a commercial relationship.** One without the other is worth little: a filled-in governance pack with no contract is unbillable, and a commercial agreement with no assurance evidence cannot pass a railroad's security review.

## 6. Merged architecture — proposal

Three concentric rings rather than a flat list of 21 documents:

**Ring 1 — Commercial & Legal (ours, keep).** A1 ROI, A2 Rate Card, D01 Preface, D02 Pilot, D03 MSA, D04 SOW, D05 Rollover, D07 Master Contract, D08 Licensing, D09 DPA, D11 NDA, D12 Regulatory Status.

**Ring 2 — Technical (ours + library shape).** B01 Blueprint, B02 Flow Map, B03 Infographic, B04 Stack, B05 Data Flow. Add: B06 Physics V&V (replaces their "AI validation" in the correct sense).

**Ring 3 — Assurance & Governance (mostly from the library).** C01 Deployment SOP, C02 Certification (plus competency verification), C03 **Pilot Authorization Gate**, C04 Rollback & Recovery, E01 **Evidence Register & Hash Manifest**, E02 **Chain of Custody & Air-Gap Media**, E03 **DR with RTO/RPO**, E04 Continuous Compliance, E05 Records Retention, E06 Governance RACI.

**Net change: 21 → ~29 documents.** Eleven adopted or reformed from the library, one rejected on principle (ownership transfer), nine rejected as out of domain.

## 7. The strategic point underneath all of this

If a competitor walks into a Class I railroad with a governance pack of this shape **fully populated**, they win on procurement maturity regardless of whose physics is better. That pack is a signal of what the buyer expects to see, and right now we would be compared against it with an RSS feed and three markdown files.

The counter is not to match their paperwork volume. It is that **our evidence should be real while theirs is scaffolding.** Our disposition ledger, hash-chained, with registry-bound reviewer identity, genuinely produces the artefact their MER and MHMR are trying to describe. That is the story: *we do not have a governance binder because we are the governance binder.* But that claim only holds if we also run our own delivery to that standard — which means E01 and E02 are not optional paperwork, they are the proof of concept for the product itself.

---

## 8. Recommended immediate sequence

1. **Record the IP decision** (§3) — blocks C01 and all D-series legal drafts.
2. **E01 Evidence Register & Hash Manifest** — closes the largest credibility gap.
3. **E02 Chain of Custody & Air-Gap Media Transfer** — the operational consequence of AD-1.
4. **C03 Pilot Authorization Gate** — the missing gate in front of D02.
5. **E03 Disaster Recovery with RTO/RPO** — required for any safety-adjacent system.
6. Then continue the D-series legal stack.

*This reconciliation is analysis, not legal advice. The IP decision in §3 is a commercial judgement for the principals and should be settled with counsel before it is written into contracts.*
