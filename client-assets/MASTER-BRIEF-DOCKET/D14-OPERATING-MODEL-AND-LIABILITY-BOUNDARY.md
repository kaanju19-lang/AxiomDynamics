# D14 — Operating Model & Liability Boundary

**Docket position:** D14. Defines how the platform is installed, operated, supported and warranted. Operative across D02 (Pilot), D03 (MSA), D07 (Master Contract), D08 (Licensing) and D12 (Regulatory Status).

> **Drafting status:** Commercial grade. Requires counsel review — particularly §4 (Liability Boundary), which is the operative clause for the entire engagement model.

---

## 1. The model in one paragraph

AxiomDynamics supplies software. The Railroad installs it, operates it, supports it and staffs it. AxiomDynamics does not access the Railroad's production environment, does not perform the deployment, and does not act as the Railroad's engineering function. AxiomDynamics supplies updates, licensing administration, and optional premium builds. The Railroad's own IT organisation, trained against our documentation, performs every operational function.

**This is a deliberate allocation, not a limitation of service.** It exists so that each party carries the risk it can actually control.

## 2. Division of responsibility

| Function | AxiomDynamics | Railroad IT | Railroad Operations |
|---|:--:|:--:|:--:|
| Software development & release | **R** | I | — |
| Security patching & update packages | **R** | **A** (apply) | I |
| Installation & configuration | C | **R/A** | I |
| Network, hardware, OS | — | **R/A** | — |
| Detector integration & data feed | C | **R/A** | I |
| Platform operation & monitoring | — | **R/A** | I |
| First-line support & service desk | — | **R/A** | — |
| Personnel training & certification | C (materials) | **R/A** | **A** (completion) |
| Advisory review & disposition | — | — | **R/A** |
| Operating decisions | — | — | **R/A** |
| Regulatory reporting | — | C | **R/A** |
| Licence administration & billing | **R/A** | I | — |
| Premium builds (optional) | **R/A** | C | I |

R = responsible, A = accountable, C = consulted, I = informed.

**AxiomDynamics has no 'A' anywhere in the operational column.** That is the point of the model, and it must be visible to the Railroad's counsel in exactly this form.

## 3. What AxiomDynamics does not do

Stated affirmatively, because silence on these points will later be read as an assumption of duty:

- We do not access, connect to, log into, or administer the Railroad's production environment.
- We do not perform installation, integration, configuration, or commissioning. We may observe and advise; the Railroad executes and approves.
- We do not monitor the platform in operation. We have no visibility into its runtime state.
- We do not receive alerts, advisories, or disposition records. They remain on the Railroad's system.
- We do not provide operational support, dispatch assistance, or incident response for Railroad operations.
- We do not make, communicate, or influence any train-handling or operating decision.
- We do not act as engineer of record for any Railroad system or process.
- We do not assume any obligation to detect any specific defect on any specific unit.

## 4. The liability boundary — read this carefully

**There are two distinct liabilities, and this model only addresses one of them.**

**Operational liability** arises from what happens in the Railroad's environment — a bad install, a misconfigured feed, an unpatched host, a supervisor who ignored an advisory. **Our model removes us from nearly all of this**, because we never touch the environment and never make an operating decision. This is a genuine and valuable protection.

**Product liability** arises from the software itself — a defect in the inference, an equation that under-reports risk, a failure mode that was foreseeable and not guarded against. **Self-installation does not reduce this at all.** Under US law a software vendor can be treated as a manufacturer of a product, and a manufacturer remains liable for design defects regardless of who performed the installation. If our model misses a bearing because of how we implemented the physics, the fact that the Railroad installed it on their own hardware is not a defence — and in some analyses it is worse, because we can no longer demonstrate that the deployment was correct.

**Therefore:**

- The disclaimers and limitations in D07 must target **product** liability, not merely operational liability.
- The absence of assurance must be stated as a **product characteristic**, not just a responsibility allocation.
- Professional indemnity / technology E&O coverage is required before first deployment, and the Railroad will ask for certificates during vendor qualification.

**This distinction must not be blurred in any customer-facing material.** A buyer who believes we have disclaimed *all* liability and later discovers we have only disclaimed *operational* liability will feel misled, and a court will agree with them.

## 5. The signed disposition record

On each alert, the reviewing dispatcher records a disposition. The record captures the alert as fired and the reviewer's decision, bound together by a SHA-256 fingerprint over the record content with a timestamp.

**What this record proves:**

- The alert content presented to the reviewer, unaltered since the record was created.
- Which individual recorded the decision, and their asserted certification ID.
- The decision recorded and the time it was recorded.
- **That the decision history is append-only** (AD-3, built 2026-11-09): a later decision supersedes an earlier one rather than replacing it, both survive with their own content and timestamps, and neither can be edited or deleted through the Platform or by ordinary database access.

**What this record does not prove, and must not be represented as proving:**

- **That the alert fired when the record says it fired.** A hash over content establishes integrity, not chronology. Without an external time anchor, the timestamp is only as trustworthy as the system clock.
- **That the reviewer's identity was verified.** Until the certification registry (B01 AD-2) is operational, an identifier in a field is not an authenticated identity. The record proves *what was asserted*, not *who asserted it*.
- **That the underlying physics was correct.** The record evidences the decision process, not the accuracy of the advisory.
- **That the record is tamper-proof against someone holding the database file.** Append-only closes the *superseded-without-trace* risk. It does not close the *rewritten-and-rehashed* risk: a party with write access to the file can drop the guard triggers, rewrite rows and recompute the chain. That risk needs the signed, off-box digest in design consequence 1.

**Two design consequences:**

1. **Trusted time.** For the record to carry evidentiary weight, the timestamp needs an anchor the Railroad controls — a synchronised time source inside their network, and a periodic signed digest of the ledger that fixes its state at a known moment. In an air-gapped environment this must be internal; there is no external timestamping authority available. Design this deliberately rather than assuming the clock is right.

2. **Authentication is not signature.** A hash of a record authenticates the record. It does not make it an electronic signature in the legal sense, which requires attribution to a person, demonstrated intent to sign, and a reliable association between the signature and the record. The certification registry and an explicit attestation step are what turn a record into a signature. This matters if the record is ever relied upon in a regulatory or legal proceeding.

**Note the load this record now carries.** It is simultaneously (a) the Railroad's regulatory evidence, (b) the trigger for any outcome-linked fee in D08, and (c) the asset that determines the platform's eventual valuation. A record that cannot bear all three should be described as what it is — an operational log — and not as evidence.

## 6. Configuration attestation

Because we do not install, configure or monitor, **we cannot otherwise demonstrate that a given deployment was sound.** That is an exposure, and the answer is documentation rather than presence.

At commissioning, the Railroad's IT Director signs a **Configuration Attestation** recording: hardware and OS baseline, software version and hash, detector feed sources and formats, site identifiers, network topology summary, and the identity of the personnel who performed the work.

Thereafter, every version change is recorded the same way.

**Why we require this:** it is the only mechanism by which we can later establish that a defect claim arose from the software rather than from the installation. It protects the Railroad too — it is the record that a correct deployment existed. It costs one form per deployment and it is the cheapest insurance in this document.

**What we do not get from it:** visibility. We still cannot see their system. Attestation is a snapshot at a moment in time, not monitoring. If they reconfigure afterwards without telling us, we will not know, and the attestation will be stale. The attestation therefore has a validity period and requires re-attestation on change.

## 7. Support boundary

| Category | Provided by | Included in licence |
|---|---|---|
| First-line support, service desk, triage | Railroad | — |
| Platform administration, backup, recovery | Railroad | — |
| Operational incident response | Railroad | — |
| Defect correction in the software | **AxiomDynamics** | Yes |
| Security patches | **AxiomDynamics** | Yes |
| Update packages, documented and version-controlled | **AxiomDynamics** | Yes. **Signed packaging is on the D09 §4.4 roadmap (target Q2 2027); today packages are documented and hashed in the release notes but not GPG-signed.** |
| Licence administration | **AxiomDynamics** | Yes |
| Premium / optional builds | **AxiomDynamics** | Separately priced |

**The model is software maintenance, not operations support.** That is cleaner for both parties and it must be named that way in D06, because an ambiguous support clause will be read against the supplier.

**The exposure this creates, stated plainly:** if the platform fails at 03:00 and the Railroad's team cannot restore it, the operational consequence is entirely theirs and they will feel it as our failure regardless of what the contract says. **Mitigation is documentation quality and recovery testing, not contractual language.** C01 (the self-deployment SOP, whose backup section requires the Railroad to test recovery) and F01 (site readiness, which establishes that the Railroad has the people and procedures to restore the system before we ever ship it) are load-bearing prerequisites of this model, not optional extras. **Both exist. A documented recovery-drill record is a Phase 2 assurance artifact** — see D00 Part VI. Until it exists, treat "the Railroad can restore this without us" as a design requirement we have written down, not as a tested property.

## 8. Representational discipline — the most important section

**The largest liability in this entire model is not technical. It is the gap between how the product is described in a sales conversation and what the contract says.**

If the platform is marketed as detecting failures 18–48 hours before they occur, and the contract disclaims any assurance of detection, then:

- a misrepresentation claim becomes available independent of the contract;
- the disclaimer may be argued to be inconsistent with the express representations made to induce the purchase;
- and the Railroad's procurement record will contain both documents.

**The resolution is not stronger disclaimers. It is identical language.**

Every description of the product — website, deck, email, dossier, verbal — must say the same thing the contract says:

> AxiomDynamics produces a physics-derived, ranked risk assessment for review by a qualified railroad employee. It does not detect failures with certainty, does not replace any required inspection, does not make operating decisions, and provides no assurance that any particular defect will be identified. The Railroad retains sole operating authority.

Any material saying otherwise must be withdrawn. **This is enforceable discipline or it is nothing** — one slide that says "prevents derailments" undoes the whole structure.

## 9. What this model requires from the Railroad

Stated so that the obligation is mutual and visible:

1. **Certified personnel.** Reviews performed only by individuals who have completed C02 certification and hold a current credential.
2. **Adequate resources.** Staffing sufficient to review advisories within the Railroad's own operational timeframes. An unreviewed advisory is worse than no advisory.
3. **Maintained infrastructure.** Detector hardware maintained to the Railroad's standards and AAR recommended practice; time source synchronised; hosts patched.
4. **Version currency.** Applying released security patches within a defined window. **A Railroad running an unsupported version is outside the warranty in D07** — this must be explicit.
5. **Change notification.** Informing us of configuration changes that affect the platform.
6. **Disposition discipline.** Recording a disposition for every advisory, positively or negatively, without exception. A ledger with gaps is not evidence.

## 10. Summary of residual exposure

Accepted and documented rather than hidden:

| Exposure | Status |
|---|---|
| Product liability for design defects | **Retained.** Cannot be disclaimed away. Requires insurance. |
| Loss of visibility into deployment correctness | Mitigated by Configuration Attestation, not eliminated |
| Support gap when Railroad team cannot restore service | Accepted; mitigated by documentation and recovery testing |
| Evidentiary weight of disposition records limited by clock trust | Requires trusted-time design (§5) |
| Misrepresentation from marketing/contract mismatch | **Fully controllable, and therefore inexcusable if it occurs** |

---

*Commercial and operational terms. Not legal advice. §4 and §5 require review by counsel in the relevant jurisdiction before execution. The product-liability analysis and any reliance on disclaimers must be confirmed locally.*
