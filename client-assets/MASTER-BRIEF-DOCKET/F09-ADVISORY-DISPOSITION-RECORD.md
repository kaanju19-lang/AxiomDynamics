# F09 — Advisory Disposition Record

**AxiomDynamics LLC** · Form F09 · Version 1.0 · Effective ____________ · **Retain 7 years minimum (D09 §5.1 recommends 3 for dispositions; 7 is the safer internal floor)**

**Purpose:** the record of what a Certified Reviewer decided about an advisory, when, and on what basis.

> **This is the most legally significant record the Platform produces.**
>
> After an incident, the question is never "what did the software say." It is **"did a qualified human being look at it, and what did they decide?"** This form is the answer. It is also the record that keeps AxiomDynamics in the decision-support role defined in D12 and D14, and the Customer in the operating-decision role.
>
> **A missing disposition is a breach of D02 §5 obligation 5, not an administrative lapse.** Every advisory receives one, without exception.

---

## Part 1 — Record identification

| | |
|---|---|
| Disposition ID | DISP-______ |
| Site | |
| Advisory ID | ADV-______ |
| Advisory generated (timestamp) | |
| Advisory severity (Platform ranking) | ☐ Critical ☐ High ☐ Medium ☐ Low |
| Asset identifier | |
| Detector / data source | |

---

## Part 2 — What the Platform computed

*Auto-populated by the Platform. Do not edit.*

| Parameter | Value |
|---|---|
| Ranked risk score | |
| Primary signal | ☐ Thermal ☐ Kinematic ☐ Acoustic |
| Contributing signals | |
| Threshold exceeded | |
| Data completeness at time of advisory | ☐ Complete ☐ Partial — missing: __________ |
| Model / rule version | |

---

## Part 3 — Reviewer

| | |
|---|---|
| **Reviewer name** | |
| **Certificate number** | CRT-______ |
| Certification valid on the review date? | ☐ Yes ☐ No — **STOP: uncertified reviewers may not disposition** |
| Review timestamp | |
| Time between advisory and review | ______ (hours) |

> **The certificate number is verified against the registry before the disposition is recorded.** Today this is a manual check against Form F08; when the signed certification registry is implemented (AD-2), it becomes automatic. Until then, the manual check is the control — do not skip it because it is manual.

---

## Part 4 — Disposition

Select **one**. The categories below are the only permitted values; free text alone is not a disposition.

### ☐ ACCEPTED — the Platform's assessment warranted action

| | |
|---|---|
| Action taken | ☐ Car set out ☐ Inspected, no defect found ☐ Inspected, defect confirmed ☐ Reduced speed ☐ Other: ______ |
| Was a defect found? | ☐ Yes — describe: __________ ☐ No |
| Was the action consistent with existing process? | ☐ Yes ☐ No — explain: __________ |

### ☐ REJECTED — the Platform's assessment did not warrant action

| | |
|---|---|
| Reason for rejection | ☐ Detector data anomaly ☐ Known condition, previously inspected ☐ Assessment implausible on engineering grounds ☐ Within normal operating envelope ☐ Other: ______ |
| Explanation (required) | ____________________________________________ |
| **Was this caused by Platform behaviour or by data?** | ☐ Platform ☐ Data quality ☐ Configuration ☐ Unknown |

> **The last line is the one that matters commercially.** Rejections attributed to Platform behaviour count toward the false-positive rate in D06 §4 and may trigger service credits. Rejections attributed to data quality or configuration do not. Answer it honestly — an inflated attribution to data quality would be discovered in the quarterly reconciliation, and would cost more in credibility than the credit is worth.

### ☐ DEFERRED — further information is required

| | |
|---|---|
| What is required | |
| Deferred until | |
| Re-review date | |
| **Maximum deferral** | 14 days — after which a decision must be recorded |

> A deferral is not a decision. A disposition may not remain deferred past 14 days; the record must resolve to Accepted or Rejected.

---

## Part 5 — Reviewer's own words

*Optional but valuable. The reviewer's reasoning in their own words is the most persuasive evidence in any later review of this decision.*

________________________________________________________________

________________________________________________________________

---

## Part 6 — Boundary confirmation

**The reviewer confirms, by signing:**

☐ I am the person named in Part 3, and I reviewed this advisory myself.
☐ I did not consult AxiomDynamics personnel for an **operating recommendation**. *(We would have declined — D06 §1.4.)*
☐ My decision was made under the Customer's own operating rules and authorities.
☐ I understand this record is **intended to be append-only** — corrections are made by a new record referencing this one, never by editing. *(As of this form's version, the write path still allows overwrite; see Part 7, disclosure 1.)*

---

## Part 7 — Signature and integrity

| | |
|---|---|
| Reviewer signature | |
| Timestamp (system) | |
| Record hash (SHA-256) | |
| Hash of preceding record | |

> **Two disclosures on this block, stated plainly rather than implied.**
>
> **1. The append-only claim is not yet implemented.** The current write path overwrites a record if one exists for the same advisory (B01 §7, blocking gap #2; D09 §4.4). Until the ledger is rebuilt as insert-only, this form describes the *required* behaviour, and the ledger is a record rather than an audit trail. **Do not represent it as tamper-evident until that is fixed.**
>
> **2. A hash is not a signature.** The SHA-256 field demonstrates that the record has not changed since it was written. It does **not** prove who wrote it, because the Platform's authentication is local accounts rather than cryptographically registered credentials (AD-2 not yet built). A hash proves integrity, not identity. Anyone relying on this record in a legal proceeding should understand the difference.

---

## Part 8 — Correction record

*Used only to correct an error in a signed disposition. The original is never edited.*

| | |
|---|---|
| Corrects disposition | DISP-______ |
| Nature of the correction | |
| Reason | |
| Corrected by (must be the original reviewer, or an Administrator with the reason recorded) | |
| Date and time | |

---

## Part 9 — Monthly summary (completed by the Customer)

| | |
|---|---|
| Month | |
| Advisories generated | |
| Dispositions recorded | |
| **Coverage (dispositions ÷ advisories)** | ______ % — **must be 100%** |
| Accepted | |
| Rejected — Platform-attributed | |
| Rejected — data or configuration-attributed | |
| Deferred outstanding | |
| **False-positive rate** (Platform-attributed ÷ total) | ______ % — compare to D06 §4.3 |

**Submitted to AxiomDynamics on:** __________

> The monthly summary is what feeds the quarterly false-positive reconciliation (D06 §4.2). A month with coverage below 100% is a compliance issue before it is a statistics issue: an advisory nobody dispositioned is an advisory nobody acted on.

---

*Form F09. Uncontrolled when printed. Append-only by design; current implementation overwrites — see Part 7.*
