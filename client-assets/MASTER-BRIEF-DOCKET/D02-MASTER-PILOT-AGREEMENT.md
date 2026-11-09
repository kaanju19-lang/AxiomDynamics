# D02 — Master Pilot Agreement

**Docket position:** D02. The entry contract. Executed under D03 (MSA) where one is in place, otherwise standing alone with D07 incorporated by reference.

> **Drafting status:** Commercial grade. Requires counsel review before execution. Fees in this document are illustrative for a single-yard pilot and must be replaced with a completed A2 Rate Card before signature.

---

## 1. Parties and term

Between AxiomDynamics ("Supplier") and __________________ ("Railroad").

**Pilot term:** ____ months from the Commissioning Date (§5), not exceeding twelve (12) months without written extension.

**Pilot scope:** one (1) site, being __________________, covering up to ____ monitored axles.

**Nature of the engagement:** evaluation and validation. **This is not a production deployment.** No ongoing operation is authorised under this Agreement; production use requires the licences in D08.

## 2. What the Railroad is buying

A licence to operate the platform at the pilot site for the pilot term, together with the documentation, training materials and update packages described in §4.

**What the Railroad is not buying:** any assurance that the platform will detect any particular defect, prevent any particular incident, or achieve any particular financial outcome. See §7 and D12.

## 3. Fees

| Component | Amount (USD) | Notes |
|---|---:|---|
| Pilot licence (12 months, one site) | $180,000 | Non-exclusive, on-premise |
| Implementation support & commissioning assistance | $65,000 | Advisory only — Railroad performs installation (D14) |
| Training materials & certification programme | $40,000 | Materials and curriculum; Railroad delivers training |
| Validation support | $35,000 | Historical data comparison, methodology review |
| Support during pilot | $50,000 | Defect correction, patches, licence administration |
| **Total pilot fee** | **$370,000** | Invoiced per §3.2 |

**3.2 Payment:** 40% on signature, 30% on Commissioning Date, 30% on completion of month six. Invoiced in USD, net thirty days.

**3.3 Pilot fee credit:** on conversion to a production licence under D05 within ninety days of pilot expiry, **fifty percent (50%) of the pilot licence fee ($90,000) is credited** against the first production term. No other component is creditable.

**3.4 Taxes:** exclusive of all taxes; the Railroad bears sales, use, VAT and withholding.

## 4. Supplier obligations

1. Deliver the software, documentation and training materials in §3 and B01.
2. Provide update packages and security patches during the term, per D06.
3. Provide advisory support during installation, **without performing installation** (D14 §3).
4. Maintain the licence and certification registry infrastructure described in B01.
5. Meet the response commitments in D06.
6. Deliver the pilot evaluation report at §8.

**No obligation to monitor the platform, access the Railroad's environment, or provide operational support** (D14).

## 5. Railroad obligations

1. Perform installation, integration, configuration and commissioning, using its own personnel (D14).
2. Sign the Configuration Attestation on commissioning (D14 §6).
3. Designate a Pilot Sponsor and a technical contact with authority to act.
4. Ensure personnel who review advisories complete certification (C02).
5. Record a disposition for every advisory generated during the pilot, without exception.
6. Provide the historical data reasonably required for the §8 evaluation.
7. Comply with the licence restrictions in D13 §7.
8. Maintain the pilot environment and detector feed in working order.

**Commissioning Date** means the date the Railroad signs the Configuration Attestation confirming the platform is operational at the pilot site. **Supplier has no responsibility for delay in achieving the Commissioning Date.**

## 6. Pilot scope limits

The pilot is limited to the site and axle count in §1. It is **not** authorised for:

- Use in any production decision-making process without the Railroad's own internal approval;
- Any site other than the pilot site;
- Any integration into a control, signal or protection system;
- Reliance as a substitute for any required inspection or detector (D12 §3).

**Advisory output during the pilot is for evaluation. The Railroad's existing processes and regulatory obligations remain unchanged and unaffected.**

## 7. Warranties and disclaimers

**7.1 Supplier warrants:** it has the right to grant the licences; the software will perform materially in accordance with the documentation in B01; it will provide the services with reasonable skill and care; and it will not knowingly introduce malicious code.

**7.2 Supplier does not warrant:** that the software will be error-free; that it will detect any particular defect or type of defect; that it will identify any particular proportion of failures; that it will prevent any incident, derailment, or damage; that results obtained will meet the Railroad's requirements; or that any indicative performance figure will be achieved on the Railroad's data.

**7.3 THE SOFTWARE IS PROVIDED "AS IS" SUBJECT ONLY TO §7.1. SUPPLIER MAKES NO OTHER WARRANTY, EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.**

**7.4 Express acknowledgement.** The Railroad acknowledges it has read D12 and D14, understands that the platform is a decision-support tool and not a certified safety appliance, does not satisfy any WDBD requirement, and that its operating decisions and regulatory obligations remain entirely its own.

**7.5 Reliance.** The Railroad confirms it has not relied on any statement, projection, demonstration or representation not expressly set out in this Agreement.

## 8. Evaluation and success criteria

Within thirty days of pilot expiry, Supplier delivers a written evaluation report covering: advisories generated; dispositions recorded; conditions identified that the incumbent process had not surfaced, as corroborated by the Railroad's own records; false-positive volume; and operational observations.

**The report presents observed outcomes on the pilot data. It does not extrapolate to a financial return, and the Railroad's decision to proceed is its own commercial judgement.**

**The criteria below are evaluation criteria, not performance guarantees. Failure to meet any of them does not constitute breach of this Agreement.**

| Criterion | Target |
|---|---|
| Advisories reviewed and dispositioned | 100% of advisories generated |
| Conditions surfaced not previously identified | To be observed and recorded |
| False-positive rate | To be measured; no target |
| Platform availability | To be measured; no target |
| Reviewer certification completed | 100% of designated reviewers |
| Configuration Attestations current | 100% |

**Rationale for the absence of targets:** the pilot exists to discover the platform's actual behaviour on the Railroad's data. Setting pass/fail targets before measuring invites both parties to argue about the target rather than the result.

## 9. Intellectual property

As set out in **D13**, which governs: Supplier retains all IP; the Railroad owns its data; escrow is insolvency-triggered and grants operability only. The Railroad acquires **no** ownership of the software, models or documentation during or after the pilot.

**Pilot data:** the Railroad may retain all data generated at the pilot site, including dispositions, after expiry, in usable export format.

## 10. Confidentiality

Governed by D11, which survives this Agreement.

## 11. Open-source and third-party components

Per B04, the only third-party runtime dependency is numpy (BSD-3-Clause). No component requires disclosure of Supplier's source code or restricts the licensing model. Supplier discloses any change to this inventory before delivery (D10).

## 12. Liability

**12.1 Cap.** Each Party's aggregate liability under this Agreement, whether in contract, tort (including negligence), breach of statutory duty or otherwise, **shall not exceed the total pilot fee paid under §3.**

**12.2 Excluded loss.** Neither Party is liable for loss of profit, revenue, business, anticipated savings, goodwill, data (save for the cost of restoration from backup), or any indirect or consequential loss, however arising.

**12.3 Unlimited items.** Nothing in §12 limits liability for: death or personal injury caused by negligence; fraud or fraudulent misrepresentation; breach of confidentiality; infringement of the other Party's IP; or any liability that cannot lawfully be limited.

**12.4 The product-liability position, stated openly.** The Parties acknowledge that §12.1 caps contractual liability for the pilot. **It does not, and cannot, exclude a claim in tort arising from personal injury or property damage caused by a defective product**, and the Parties do not purport to do so. This limitation is a contractual allocation between commercial parties, not a representation that no other liability can arise.

*This clause is the most important in the document and the most likely to be tested. It requires counsel review before execution.*

## 13. Indemnities

**13.1 Supplier indemnifies** the Railroad against third-party claims that the software, as supplied and used within its licence, infringes a third party's IP rights, subject to §12.

**13.2 Railroad indemnifies** Supplier against third-party claims arising from the Railroad's operation of its railway, its operating decisions, its detector infrastructure, its failure to comply with regulatory obligations, or its use of the software outside its licence.

## 14. Independent contractor

Supplier is an independent contractor. Nothing creates a partnership, joint venture, agency or employment relationship. **Neither Party's personnel are under the direction or control of the other.** See D14 §3.

## 15. Termination

**15.1 For convenience:** either Party on thirty days' written notice.

**15.2 For cause:** either Party on thirty days' written notice of a material breach not cured within that period.

**15.3 For insolvency:** either Party immediately on the other's insolvency, administration, or cessation of business.

**15.4 Effect:** the Railroad ceases use, exports its data in usable format, and remains liable for fees accrued to termination. §9, §10, §12, §13 and §16 survive.

**15.5 Escrow on termination:** termination of this Agreement does **not** trigger escrow release. Release arises only on the conditions in D13 §4.

## 16. Dispute resolution

Good-faith negotiation between authorised representatives for thirty days, followed by mediation, before either Party commences proceedings — save for applications for injunctive relief, which may be brought at any time.

## 17. General

Entire agreement (with the documents incorporated by §18); supersedes prior discussions; amendments only in writing; no waiver by delay; severability; no third-party beneficiaries; notices in writing to the addresses below; neither Party may assign without written consent save under D13 §6.

## 18. Incorporated documents

This Agreement incorporates by reference: **D11** (NDA), **D12** (Regulatory Status), **D13** (IP & Escrow), **D14** (Operating Model), **B01** (Blueprint), **B04** (Tech Stack), **B05** (Data Flow), **D06** (Support & SLA), **C01** (Deployment SOP), **C02** (Certification).

Where a conflict exists, the order of precedence in D00 Part IV applies.

---

## Signatures

**AxiomDynamics**

Name: __________________  Title: __________________

Signature: __________________  Date: __________________

**Railroad**

Name: __________________  Title: __________________

Signature: __________________  Date: __________________

---

*Form of agreement. Not legal advice. Every provision must be reviewed by counsel in the governing jurisdiction before execution. Fees are illustrative and must be confirmed against A2 before signature.*
