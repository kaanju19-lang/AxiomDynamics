# D07 — Comprehensive Master Contract

**Docket position:** D07. The umbrella agreement. Governs generally, survives individual orders, and is the reference for every other document in this docket.

> **Drafting status:** Commercial grade. **Requires review by qualified counsel in each jurisdiction of deployment before execution.** Sections 8 (Liability), 9 (Indemnity), 10 (Insurance) and 14 (Dispute Resolution) are the provisions most likely to be tested and most likely to require local variation.

---

## 1. Definitions

Terms defined here apply throughout the docket. Where a term is defined in a specific document and used only there, that document's definition governs.

**Advisory** — a ranked, physics-derived condition assessment produced by the Platform for review by a Certified Reviewer. Not an instruction, order, or operating authority.

**Certified Reviewer** — an individual who has completed the certification programme in C02, holds a current credential, and is authorised by the Railroad to record dispositions.

**Commissioning Date** — the date the Railroad signs the Configuration Attestation confirming operational status at a site.

**Configuration Attestation** — the record defined in D14 §6.

**Disposition** — the record of a Certified Reviewer's decision in respect of an Advisory.

**Platform** — the AxiomDynamics software, including all modules, models, rules, documentation and updates supplied under this Agreement.

**Railroad Data** — all data owned by the Railroad under D13 §3, including sensor data, derived condition data, Advisories, Dispositions, and reports.

**Site** — a monitored location at which the Platform is installed, as defined in A2.

**Supplier IP** — all intellectual property owned by AxiomDynamics under D13 §3.

## 2. Structure of the agreement

This Agreement is the umbrella. Individual engagements are ordered under it:

- **D02 Master Pilot Agreement** — pilot engagements
- **D04 Statement of Work** — scoped deployment orders
- **D08 Master Licensing and Liability** — production licences
- **A2 Rate Card** — pricing

Each order is a separate contract incorporating this Agreement. **No order varies this Agreement unless it expressly states an intention to do so and identifies the clause.** A term sheet, email, purchase order, or vendor form does not vary this Agreement.

## 3. Scope of licence

**3.1 Grant.** Subject to payment and compliance, Supplier grants the Railroad a non-exclusive, non-transferable, non-sublicensable licence to install and use the Platform at the licensed Sites, for the Railroad's own internal railway operations, for the licence term.

**3.2 No ownership.** The Railroad acquires no ownership of the Platform, models, or documentation. See D13.

**3.3 Restrictions.** The Railroad shall not, and shall ensure its personnel and contractors do not: copy the Platform except for backup and disaster recovery; modify or create derivative works except on an escrow-released version under D13 §4; reverse engineer except as permitted by D13 §4 or non-waivable law; sublicense, distribute, or provide access to any third party; use the Platform to develop or benchmark a competing product; remove proprietary notices.

**3.4 Third-party components.** Per B04 and D10. Supplier warrants no component requires disclosure of Supplier's source or restricts the licence model in §3.1.

## 4. Supplier obligations

1. Deliver the Platform and documentation as described in B01 and B04.
2. Provide updates and security patches per D06.
3. Maintain the certification and licence registry infrastructure per B01.
4. Provide the advisory support described in D14 §3, without performing installation or operating functions.
5. Meet the support commitments in D06.
6. Notify the Railroad of any security vulnerability materially affecting the Platform, per §7.

## 5. Railroad obligations

1. Install, configure, and operate the Platform using its own personnel (D14).
2. Sign and maintain Configuration Attestations (D14 §6).
3. Ensure only Certified Reviewers record Dispositions.
4. Record a Disposition for every Advisory, without exception.
5. Maintain its detector infrastructure to its own standards and AAR recommended practice.
6. Maintain the Platform's host environment, including OS patching and time synchronisation.
7. Apply Supplier security patches within the window defined in D06.
8. Notify Supplier of configuration changes materially affecting the Platform.
9. Comply with all regulatory obligations, which remain entirely its own (D12 §4).

## 6. Detector data — the integration dependency

**This section allocates a risk that is otherwise ambiguous in both directions.**

**6.1 The Railroad warrants** that its detector hardware is installed, calibrated, maintained and inspected in accordance with its own standards and applicable recommended practice, and that data supplied to the Platform is the genuine output of that equipment.

**6.2 The Supplier warrants** that it processes that data in accordance with the models described in B01, without introducing error of its own.

**6.3 Neither party warrants the other's equipment or processes.** Supplier is not responsible for a missed defect caused by a detector that was not producing accurate data, provided the Platform processed the data it received correctly. The Railroad is not responsible for a Platform error that occurs on accurate input.

**6.4 Evidence.** Where a missed defect is alleged, the Configuration Attestation, the detector maintenance records and the Platform's processing logs together determine which party's domain the failure falls in. **This is the reason the Configuration Attestation is mandatory rather than advisory.**

## 7. Data protection and security

**7.1 No off-network processing.** The Platform does not transmit Railroad Data outside the Railroad's network (B05). Supplier receives no Railroad Data in normal operation.

**7.2 Data ownership.** Per D13 §3. The Railroad may export its data in usable format at any time and on termination.

**7.3 Security programme.** Supplier maintains a documented secure development practice and reviews dependencies for known vulnerabilities. **Supplier will produce an SBOM with each release once generation is implemented (target Q1 2027); it is not produced today.** The current component inventory is published in **D10** and may be independently verified by the Railroad against the installed packages (D09 §10.2). **The obligations in this clause are limited to what is actually performed**, and D09 §4.4 discloses the remaining gaps. A contractual obligation to deliver an artefact that does not exist is a breach waiting for a date.

**7.4 Vulnerability notification.** Supplier notifies the Railroad in writing of any vulnerability it identifies that materially affects the Platform, within **five (5) business days** of confirmation, together with severity and remediation plan. Critical vulnerabilities are notified within **forty-eight (48) hours**.

**7.5 Incident notification.** If Supplier becomes aware of a security incident affecting the Platform or Railroad Data — including one occurring at Supplier — it notifies the Railroad without undue delay and in any event within **seventy-two (72) hours**, providing what is known, what is affected, and containment steps.

**7.6 Post-incident.** Supplier provides a written root-cause analysis within thirty days of containment, and remediation commitments.

**7.7 Personnel security.** Personnel with access to Supplier IP related to the Platform are subject to background verification consistent with applicable law. **Supplier personnel do not require access to Railroad systems**, since Supplier performs no installation or operating function. Where the Railroad requires its own screening for any on-site visit, Supplier will accommodate it.

**7.8 Audit.** Once per year, on thirty days' notice, the Railroad may audit Supplier's compliance with §§7.3–7.7, either directly or through an independent auditor bound by confidentiality. Scope is limited to the Platform and does not extend to Supplier's other customers or products.

## 8. Liability

**8.1 Cap.** Subject to §8.3, each party's total aggregate liability arising under or in connection with this Agreement, whether in contract, tort (including negligence), breach of statutory duty or otherwise, shall not exceed **the fees paid or payable by the Railroad in the twelve months preceding the event giving rise to the claim**.

> **On the cap, and why there is no floor figure.** An earlier draft capped liability at "the greater of twelve months' fees **or [amount]**," with the amount left blank — and D03 §10 cross-referred to it as an operative term. **A liability clause with an unfilled limb is worse than no clause: it is unenforceable in the place it matters and it invites the other side to propose their own number.** The cap is now a single, complete, calculated figure — twelve months' fees — which at the pilot is $370,000 and at a 2,000-axle production licence is $1,050,000. It requires no blank to be filled and no negotiation to be settled.

**8.2 Excluded loss.** Neither party is liable for loss of profit, revenue, business, contracts, anticipated savings, goodwill, or any indirect or consequential loss, however arising, even if advised of the possibility.

**8.3 Unlimited.** Nothing in this section limits liability for: death or personal injury caused by negligence; fraud or fraudulent misrepresentation; breach of confidentiality; infringement of the other party's intellectual property; or any liability that cannot lawfully be limited.

**8.4 Product liability — stated openly.**

The parties acknowledge that §8.1 allocates contractual risk between commercial parties. **It does not, and cannot, exclude a claim in tort arising from personal injury, death, or damage to property caused by a defective product.** Nothing in this Agreement purports to exclude such liability, and no provision should be read as doing so.

**The parties further acknowledge** that the Platform is a decision-support tool (D12), that the Railroad retains sole operating authority, and that a claim arising from an operating decision made by the Railroad is governed by §8.3 and by the Railroad's own responsibility under D12 §4.

**8.5 Basis of bargain.** The fees reflect the allocation of risk in this section. The Railroad may obtain additional protection through insurance arranged at its own cost.

## 9. Indemnities

**9.1 IP indemnity.** Supplier indemnifies the Railroad against third-party claims that the Platform, used within its licence, infringes a patent, copyright, trade secret or other IP right, and will defend or settle such claims, provided the Railroad notifies promptly, gives control of the defence, and provides reasonable assistance.

**Excluded** where the claim arises from: modification not made by Supplier; combination with non-Supplier products; use outside the licence; or the Railroad's own data.

**9.2 If enjoined.** Supplier may, at its option: procure the right to continue use; modify the Platform to be non-infringing while materially preserving function; or terminate the licence and refund prepaid fees for the unexpired term. **This is the Railroad's sole remedy for IP infringement.**

**9.3 Railroad indemnity.** The Railroad indemnifies Supplier against third-party claims arising from its operation of its railway, its operating decisions, its detector infrastructure, its regulatory non-compliance, or its use of the Platform outside its licence.

**9.4 Procedure.** Notice promptly; indemnitee cooperates; indemnitor controls defence; no settlement admitting liability without consent.

## 10. Insurance

Supplier maintains, with insurers of good standing, during the term **and for twenty-four (24) months after**:

| Cover | Minimum |
|---|---|
| Commercial general liability | $[1,000,000] per occurrence / $[2,000,000] aggregate |
| **Technology errors & omissions / professional indemnity** | **$[2,000,000]** per claim |
| Cyber liability | $[1,000,000] per claim |
| Workers' compensation | Statutory |
| Employer's liability | $[1,000,000] |
| Umbrella / excess | As available (see note) |

Certificates furnished on request and on renewal. Insolvency of an insurer does not relieve the obligation to maintain cover.

*Technology E&O is the essential line and is not optional. It is the cover that responds to the product-liability exposure in §8.4 that the contract cannot exclude. A Class I vendor-qualification process will request the certificate.*

### 10.1 The insurance limit is set to what can actually be bought

**This is stated openly rather than papered over, because a contract that promises cover the Supplier cannot purchase is worse than no promise at all — it is discovered at exactly the moment it is relied upon.**

A pre-revenue supplier cannot obtain $5,000,000 of Technology E&O at a premium the business can carry. Underwriters price professional liability on revenue, contract value, and loss history. At the Effective Date the purchasable limit is **$2,000,000 per claim**, and that is the limit stated above.

**The commitment is therefore twofold:**

1. Maintain Technology E&O of not less than **$2,000,000 per claim** from the Effective Date.
2. **Increase the limit as the business grows**: on the first renewal following either (a) annual recurring revenue exceeding $1,000,000, or (b) execution of a production licence under D08, Supplier will obtain the highest limit then commercially available up to $5,000,000, and will provide the certificate to the Railroad within thirty days.

**The Railroad may verify this** by requesting the certificate at any renewal (§7.8 audit rights extend to insurance compliance). *Provided the certificate matches this clause.* The bracket notation in the table above is completed before execution, not after — an unbracketed figure that matches no certificate is the failure mode this clause exists to prevent.

**Amended:** D03 §9 states the same limits. Where this clause and D03 §9 differ, this clause governs.

## 11. Intellectual property

Governed by **D13** in full: ownership, escrow, assignment, contributor assignments, trade secrets, and third-party components. Nothing in this Agreement alters D13.

## 12. Representations and warranties

**12.1 Each party** represents that it has authority to enter this Agreement and is not in breach of any obligation by doing so.

**12.2 Supplier warrants:** title and authority to license; performance materially in accordance with documentation; services performed with reasonable skill and care; no knowingly introduced malicious code; compliance with §7.

**12.3 No other warranty.** **THE PLATFORM IS PROVIDED "AS IS" SUBJECT ONLY TO §12.2. SUPPLIER MAKES NO OTHER WARRANTY, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR PURPOSE, ACCURACY OF OUTPUT, OR NON-INFRINGEMENT.**

**12.4 No performance warranty.** Supplier does not warrant that the Platform will identify any particular defect or proportion of defects, prevent any incident, or achieve any indicated outcome. **All performance figures are indicative estimates based on stated assumptions, not commitments.** See D12 §8.

**12.5 Regulatory acknowledgement.** The Railroad acknowledges it has read D12 and understands the Platform is not a certified safety appliance, does not satisfy any WDBD requirement, and does not relieve the Railroad of any obligation.

## 13. Export control and sanctions

**13.1** Each party complies with applicable export control and economic sanctions laws.

**13.2** The Railroad confirms it is not located in, owned or controlled by a person in, a comprehensively sanctioned jurisdiction, and is not a denied party.

**13.3** Supplier confirms the Platform contains no encryption beyond that supplied by the operating system and standard libraries, to Supplier's knowledge, that would require export authorisation.

**13.4** The Railroad shall not export the Platform to any jurisdiction requiring authorisation without obtaining it.

## 14. Dispute resolution

**14.1 Negotiation.** Authorised representatives negotiate in good faith for thirty (30) days from written notice of dispute.

**14.2 Mediation.** If unresolved, mediation under [the mediation rules of the chosen provider] before a single mediator, for a further thirty (30) days.

**14.3 Proceedings.** If unresolved, [the courts / arbitration seat] stated in the Order signature block________ have exclusive jurisdiction. **Either party may seek injunctive relief at any time** to protect confidentiality or IP.

**14.4 Continuing performance.** Both parties continue to perform during a dispute, and the Railroad continues to pay undisputed amounts.

## 15. Term, termination, and exit

**15.1 Term.** This Agreement begins on execution and continues until terminated.

**15.2 Termination for cause.** Either party on thirty days' notice of material breach uncured.

**15.3 Termination for insolvency.** Immediately on insolvency, administration, or cessation of business of the other.

**15.4 Termination for convenience.** Either party may terminate **this Agreement** on **ninety (90) days'** written notice; termination of this Agreement terminates all orders placed under it, subject to §15.5 and §15.6. An individual order may also be terminated for convenience on the notice period stated in that order.

> **Corrected.** An earlier draft of this clause said the Agreement "does not terminate for convenience while an order is in force," which contradicted D03 §12.1 (90 days' convenience termination terminating all orders). The two instruments cannot both be right. **The position is now consistent:** either party may exit the whole relationship on 90 days' notice, and individual orders carry their own convenience terms — including D05 §9.1, which permits the Railroad to terminate a production licence for convenience on 60 days' notice in Year 1 at no penalty. A customer who cannot exit is a customer who will not enter.

**15.5 Effect.** Licences in the terminated order cease; the Railroad ceases use; the Railroad exports its data in a documented, usable format; fees accrued remain payable.

**15.6 Transition assistance.** On termination for any reason other than the Railroad's uncured breach, Supplier provides, for **ninety (90) days** at no additional charge: export of Railroad Data in documented machine-readable format; reasonable assistance in transitioning to another solution or to a self-maintained escrow-released version; and a written statement of the Platform's configuration and version at termination.

**15.7 Retention.** After the transition period, Supplier destroys any Railroad Data it holds and certifies destruction. Under AD-1, Supplier holds none in normal operation; this applies to any data received for support.

**15.8 Survival.** §§1, 3.2, 3.3, 7.2, 8, 9, 11, 15.5–15.8, 16 and 17 survive.

## 16. Certification and competency

**16.1** Supplier issues certification through the programme in C02. **Certification evidences completion of training and assessment against Supplier's curriculum. It is not a guarantee of an individual's performance and creates no liability for any act or omission of a Certified Reviewer.**

**16.2** The Railroad retains all employment, supervision, and competence responsibility for its personnel. **The Railroad is solely responsible for the acts and omissions of its Certified Reviewers.**

**16.3** The Railroad revokes certification authority on personnel changes and notifies Supplier.

## 17. General

**17.1 Entire agreement.** This Agreement with its incorporated documents is the entire agreement and supersedes prior discussions, save for fraud.

**17.2 Order of precedence.** As set out in D00 Part IV.

**17.3 Variation.** Only by written instrument signed by both parties expressly varying this Agreement.

**17.4 No waiver.** Failure to enforce is not waiver.

**17.5 Severability.** Unenforceable provisions are severed; the remainder survives.

**17.6 No partnership or agency.** Independent contractors (D14 §2–§3).

**17.7 Assignment.** Per D13 §6.

**17.8 Third parties.** No third-party rights, save as expressly stated.

**17.9 Notices.** Formal notices are given on **Form F12**, which governs the method and the moment of effectiveness. Addresses as stated in the Order, or where no Order states them, as stated in **D03 §17**.

> **Why this points at D03 rather than repeating an address block.** Two instruments that each carry an address block will eventually carry two different ones, and a notice sent to the wrong one is ineffective for reasons nobody intended. **One address block, one document.** D03 §17 is where the executed addresses live.

**17.10 Publicity.** Neither party names the other publicly without written consent, save that Supplier may identify the Railroad as a customer once the first production licence is in force and the Railroad has approved the form of reference. **Pilot participation alone does not create reference rights** — reference rights arise only at the Stage II brand-licence stage in the ownership schedule at **D13 §2**.

**17.11 Force majeure.** Neither party is liable for failure caused by events beyond reasonable control, excluding payment obligations. Prolonged force majeure over sixty days permits termination of the affected order.

**17.12 Counterparts and electronic signature.** May be executed in counterparts and by electronic signature.

## 18. Incorporated documents

D11 (NDA) · D12 (Regulatory Status) · D13 (IP & Escrow) · D14 (Operating Model) · D02 (Pilot) · D08 (Licensing) · D06 (Support & SLA) · B01 · B04 · B05 · C01 (Deployment SOP) · C02 (Certification) · D09 (DPA) · D10 (Components) · A2 (Rate Card).

---

## Signatures

**AxiomDynamics**

Name: __________________  Title: __________________

Signature: __________________  Date: __________________

**Railroad**

Name: __________________  Title: __________________

Signature: __________________  Date: __________________

---

*Form of agreement. Not legal advice. Must be reviewed by counsel in each jurisdiction before execution. Bracketed figures are drafting placeholders and must be set deliberately. §§8, 9, 10 and 14 require particular local attention.*
