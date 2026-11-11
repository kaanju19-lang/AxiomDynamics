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

> **The certificate number is verified against the registry before the disposition is recorded.** Today this is a manual check against Form F08; since 2026-11-11 the Platform can also carry an attestation from a registered reviewer key inside the exported record (AD-2, partly built — B01 §7 item 1), but **entry is not yet gated on one**, so the manual check is still the control. An attestation, where present, lets a recipient verify which registered key vouched for the row; it does not prove the person at the keyboard was the certified reviewer. Do not skip the manual check because it is manual.

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
☐ I understand this record is **append-only** — a correction creates a new record that references this one, and this record is never edited or deleted. *(Implemented 2026-11-09; the database refuses `UPDATE` and `DELETE` on the ledger. See Part 7, disclosure 1, for what this does and does not prove.)*

---

## Part 7 — Signature and integrity

| | |
|---|---|
| Reviewer signature | |
| Timestamp (system) | |
| Record hash (SHA-256) | |
| Hash of preceding record | |

> **Three disclosures on this block, stated plainly rather than implied.**
>
> **1. The append-only claim is implemented as of 2026-11-09.** Each disposition is written as a new row; a correction records a `supersedes_id` pointing at the row it corrects, and the earlier row keeps its own content and timestamp. `UPDATE` and `DELETE` against the ledger are refused by the database itself, and every row carries a SHA-256 over its content and its predecessor's hash. What that proves is bounded: it proves the record cannot be altered through the application or by ordinary database access, and that an alteration made by bypassing those guards is detectable.
>
> **2. A hash is not a signature.** The SHA-256 field demonstrates that the record has not changed since it was written. It does **not** prove who wrote it, because the Platform's authentication is local accounts rather than cryptographically registered credentials (AD-2 not yet built). A hash proves integrity, not identity. Anyone relying on this record in a legal proceeding should understand the difference.
>
> **3. The ledger can be exported as a verifiable bundle, and that is not the same as a signed certificate.** Since 2026-11-09 the ledger exports as a signed bundle that a third party can verify without the Platform's software or access to the database. It detects altered, added, removed and reordered records, and a ledger that has shrunk since a bundle already held. The signature is HMAC-SHA256 — symmetric — so it proves the bundle is authentic but cannot name the signer or prove when it was made, and a ledger wiped before the first bundle in a series cannot be detected from later ones. Off-box replication is still manual. Those limits are open in D09 §4.4–4.5 and are expected to close with AD-2. **Do not describe an export as a certificate of authorship.**

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

*Form F09. Uncontrolled when printed. Append-only — enforced by the database and hash-chained; the ledger exports as a signed bundle that a third party verifies without the Platform. The signature cannot yet name the signer. See Part 7.*
