# D12 — Regulatory Status & Safety-Critical Function Statement

**Docket position:** D12. The single authoritative statement of the platform's regulatory status. Where any other document in this docket describes the platform's function, this document controls.

> **Drafting status:** Commercial grade. Requires counsel review, and review against the regulatory regime of each jurisdiction where deployed.

---

## 1. What the platform is

AxiomDynamics is a **decision-support and information system**. It computes physics-derived condition estimates from wayside sensor data and presents a ranked risk assessment to a qualified human reviewer, who records a disposition.

It is an aid to human judgement. It is not a substitute for judgement, and it does not exercise judgement.

## 2. What the platform is not

Stated exhaustively, because each of these has been assumed by a customer somewhere and each assumption creates a liability:

- **Not a certified safety appliance.** It holds no certification, type approval, or accreditation from the Federal Railroad Administration, Transport Canada, the Agencia Reguladora del Transporte Ferroviario, the Association of American Railroads, or any other body.
- **Not a wayside defective bearing detector (WDBD)** within the meaning of any regulatory instrument. See §3 — this is the most important exclusion in this document.
- **Not a substitute for any inspection, test, or maintenance action** required by regulation, rule book, carrier standard, or AAR recommended practice.
- **Not a train control, signal, or protection system.** It does not interface with, influence, or override PTC, signalling, interlocking, or any safety-critical control.
- **Not an autonomous system.** It takes no action, issues no order, communicates with no crew, and actuates nothing.
- **Not an alarm system of record.** Regulatory alarms are those produced by the Railroad's own certified detector infrastructure, under its own procedures.
- **Not a compliance determination.** It does not determine whether the Railroad has met any obligation.

## 3. The WDBD exclusion — read this carefully

This section exists because it is the most likely regulatory misconception, and the consequences of the misconception are serious.

In Canada, Transport Canada's *Rules Respecting Key Trains and Key Routes* require that a Key Train not travel more than 40 miles on a Key Route without a valid inspection by a wayside defective bearing detector. A confirmed defect triggers a codified speed restriction.

**AxiomDynamics does not satisfy that requirement, and must not be relied upon to satisfy it.**

Specifically:

- The platform is not a WDBD. It is not certified, type-approved, or recognised as one.
- It does not perform the inspection that the rule contemplates.
- It does not generate a regulatory inspection record.
- A disposition recorded in our ledger is **not** a WDBD inspection record.
- Using the platform as a substitute for required WDBD inspection would be a **regulatory non-compliance by the Railroad**, and would constitute a breach of this agreement.

The platform's value in that regime is different and real: it helps the Railroad act more effectively on the information its certified detectors already produce, and it creates a documented record of what the Railroad did with that information. **That is a management and evidentiary benefit. It is not a compliance substitute.** The distinction must be maintained in every conversation with a Canadian carrier.

## 4. Regulatory responsibility remains entirely with the Railroad

The Railroad is and remains responsible for:

- Compliance with all applicable federal, state, provincial, national and local law and regulation;
- All inspection, testing, maintenance and reporting obligations;
- All operating decisions, including whether to stop, restrict, set out, or continue;
- All crew communication and train handling;
- All filings with FRA, Transport Canada, ARTF or any other authority;
- The adequacy and maintenance of its own detector infrastructure;
- The qualification and supervision of its own personnel.

**Nothing in this docket, and nothing about the platform's function, relieves the Railroad of any obligation.** No provision of any agreement between the parties shall be construed to transfer a regulatory obligation from the Railroad to AxiomDynamics.

## 5. Human authority is absolute

The platform's output is advisory. A certified Railroad employee reviews each advisory and records a disposition. **That employee, and the Railroad, retain sole operating authority.**

AxiomDynamics does not decide. It does not recommend an operating action. It does not rank advisories in a manner intended to direct operational priority — ranking reflects estimated condition severity, not an instruction.

**No advisory, however classified, authorises or requires any action.** The reviewer may disregard any advisory without consequence under this agreement.

## 6. Jurisdictional notes

| Jurisdiction | Regulator | Platform status |
|---|---|---|
| United States | FRA; NTSB investigatory | Not certified; not a required device. HBD installation and inspection are not FRA-regulated (AAR Circular OT-55-R is recommended practice). NTSB recommendations R-24-02 to R-24-05 would, if adopted, regulate detector *hardware* — not this software. |
| Canada | Transport Canada | Not a WDBD. Does not satisfy the Key Trains rule. See §3. |
| Mexico | ARTF | Not assessed. No representation of compliance is made. Deployment in Mexico requires separate regulatory review before any commitment. |

**No representation of regulatory approval is made in any jurisdiction.** Any statement that the platform "complies with," "satisfies," "meets," or "is approved under" any regulation or standard is expressly withdrawn and must not be made by either party.

## 7. Evidentiary character of the disposition record

The disposition ledger records what was presented to a reviewer and what that reviewer decided. Its limits, stated in full in D14 §5, are summarised here because they bear on regulatory use:

- It evidences the **content** of an advisory and a recorded decision, and — **since 2026-11-09 (AD-3)** — that the decision history is append-only: a later decision supersedes rather than replaces an earlier one, both survive with their own timestamps, and neither can be edited or deleted through the Platform or by ordinary database access. It does **not** evidence that the record is signed or replicated off-box; a party with write access to the database file could rewrite it and recompute the chain. See D14 §5.
- It does **not** establish chronology independently of the Railroad's system clock.
- It does **not** establish that the reviewer's identity was verified, until the certification registry is operational.
- It does **not** evidence the accuracy of the underlying physics.
- It does **not** create a regulatory record or substitute for one.

**The Railroad may use it as supporting material in its own regulatory processes. It may not represent it as a regulatory filing, an inspection record, or a compliance certificate.**

## 8. Advertising and representational discipline

The following statements are **prohibited** in any material, communication, or presentation by either party:

- That the platform "prevents derailments" without qualification;
- That it "guarantees," "ensures," or "assures" detection of any defect;
- That it is "certified," "approved," "compliant," or "recognised" by any authority;
- That it replaces, satisfies, or is equivalent to any required inspection or detector;
- That it detects any specific proportion of failures with certainty;
- Any quantitative performance claim not accompanied by the assumptions and conditions under which it was derived.

**Permitted and accurate:** that the platform produces a physics-derived ranked risk assessment for review by qualified personnel; that in pilot evaluation it identified conditions that the incumbent process had not surfaced, on the specific data evaluated; that its purpose is to improve the quality and timeliness of human review.

**This section is enforceable discipline or it is nothing.** A single slide, email, or verbal claim to the contrary undermines the entire structure of this docket and creates a misrepresentation exposure that no disclaimer can cure. See D14 §8.

## 9. Where this document controls

Where any other document in this docket describes the platform's function or regulatory status, and that description conflicts with this document, **this document controls** and the other document is to be corrected.

Specifically, the following documents must use language consistent with §§1–3 and §5: **B01 §1, B02, B03, B05, C02, D02, D06, D07, D08, D14**, and the F-series forms that describe function (F09 Part 6, F11 Part 4).

**B02 (flow map) and B03 (one-page brief) are built and are the two documents most exposed to this rule.** §§1–3 and §5 govern their language absolutely, and both were reviewed against this section before release. **B03 is a single-page visual — the form in which a disclaimed capability most easily reappears, because a diagram asserts by implication what a sentence would have to state outright.** Its central graphic is a break in the drawn line at exactly the point where the Platform stops and a person decides. That break is the §5 requirement drawn rather than described, and any future revision that closes it is a breach of this document.

**A single slide, a single arrow, or a single caption that crosses that line** — implying the Platform decides, recommends, detects, or acts — defeats the protection this document exists to provide, and no footnote repairs it.

---

*This document states regulatory status, not legal advice. Regulatory characterisation must be confirmed with counsel and, where appropriate, with the relevant authority before any deployment in a new jurisdiction.*
