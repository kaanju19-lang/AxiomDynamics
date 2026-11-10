# F13 — Data Export & Transition Certificate

**AxiomDynamics LLC** · Form F13 · Version 1.0 · Effective ____________ · **Retain 7 years**

**Purpose:** to certify that the Customer's data has been exported in usable form and that the transition obligations under D07 §15.6 have been discharged.

**Used on:** termination for any reason · non-conversion after pilot (D05 §2.2) · migration to a new platform · any point where the Customer requests a full export.

> **The question every customer asks and every vendor avoids:** *"if this ends, what do I actually get?"* This form is the answer, in specific files, in a specific format, on a specific date. Answering it before it is asked is what makes a sole-source vendor approvable.

---

## Part 1 — Reference

| | |
|---|---|
| Customer | |
| Site(s) | |
| Trigger | ☐ Termination ☐ Non-conversion ☐ Migration ☐ Customer request ☐ Other: __________ |
| Order(s) affected | |
| **Transition assistance period** | 90 days at no charge (D07 §15.6) |
| Transition start date | |
| Transition end date | |
| Export reference | EXP-______ |

---

## Part 2 — What is exported

**Complete each line. A line left blank is a data category the Customer should ask about.**

| # | Data category | Format | Records | Delivered | Reference |
|---|---|---|---:|---|---|
| 1 | Advisory records | CSV + JSON | | ☐ | |
| 2 | Disposition records (full ledger) | CSV + JSON | | ☐ | |
| 3 | Detector data as ingested | CSV | | ☐ | |
| 4 | Configuration records | JSON + PDF | | ☐ | |
| 5 | User and certification records | CSV | | ☐ | |
| 6 | Audit log | CSV | | ☐ | |
| 7 | Support ticket history (summaries) | CSV | | ☐ | |
| 8 | Quarterly performance reports | PDF | | ☐ | |
| 9 | Configuration Attestations (F02) | PDF | | ☐ | |

**Format note:** exports are provided in **open, documented formats** (CSV, JSON, PDF) that require no AxiomDynamics software to read. An export that only the vendor's software can open is not an export.

---

## Part 3 — What is not exported, and why

State this plainly. The Customer is entitled to know the boundary before they ask.

1. **Platform source code.** Not exported. Escrow is a separate arrangement, insolvency-triggered, granting operability only (D13 §4).
2. **Models, weights, rules, and thresholds** beyond what appears in the advisory records. These are AxiomDynamics IP (D13 §3).
3. **Third-party component source** — governed by their own licences (B04).
4. **Data belonging to other customers.** Never present in this environment (B05, D09 §3).

> **Say this out loud in the transition meeting.** A customer who discovers the boundary at the end of a transition feels misled even if the contract was explicit. A customer who is told on day one respects it.

---

## Part 4 — Export verification

**4.1 Integrity:**

| | |
|---|---|
| File count | |
| Total size | |
| SHA-256 manifest provided | ☐ Yes — attached ☐ No |
| Manifest verified by Customer | ☐ Yes ☐ No |
| **Signed ledger bundle provided** (D09 §4.5) | ☐ Yes ☐ No |
| Bundle `key_id` | |
| Bundle record count / id range | |
| **Bundle verified by Customer** with `tools/verify_ledger_export.py` | ☐ Yes ☐ No |
| Verified on a machine not connected to the Platform host | ☐ Yes ☐ No |
| Prior bundle supplied as `--previous-bundle` (detects a ledger that shrank) | ☐ Yes ☐ No |

> **The ledger row above is the one that matters in a dispute.** The bundle is verified by the Customer's own staff, on the Customer's own machine, using a tool that imports nothing from AxiomDynamics — so the result does not depend on trusting the vendor. Record the `key_id`: if it ever differs from the key the Customer holds, the export was signed by someone else and the difference must be explained before this form is signed. **Verify against a bundle the Customer already holds wherever one exists** — that comparison is what detects a ledger from which records have been removed, and a first export after a wipe cannot detect it on its own. What the signature does **not** establish — authorship, and the time of signing — is set out in D09 §4.5.5 and must not be inferred from a pass.

**4.2 Usability test:** the Customer confirms it has opened at least two export files and the content is readable and complete.

☐ Tested — file 1: __________  file 2: __________  Result: __________

**4.3 Record count reconciliation:**

| | |
|---|---|
| Dispositions in Platform at export | |
| Dispositions in export | |
| **Variance** | **Must be zero. If not, explain:** __________ |
| Advisories in Platform at export | |
| Advisories in export | |
| **Variance** | |

> **A non-zero variance is a serious finding.** It means the record the Customer relied on is not the record they received. Reconcile it before signing this form, not afterwards.

---

## Part 5 — Deletion and retention

**5.1 Platform decommissioning**

| | |
|---|---|
| Platform stopped on | |
| Database file deleted on | |
| Backup media handled per | Customer's own retention policy |
| Host decommissioned on | |

**5.2 Our records**

| | |
|---|---|
| Records we retain | Contracts, orders, invoices, change orders, visit reports, certification records |
| Retained for | 7 years (F00 Part 4) |
| Reason | Legal, tax, and dispute obligations |
| **Railroad Data retained by us** | **None** — we hold no Railroad Data (D09 §3.4) |

**5.3 Certification in writing (D09 §5.2)**

> We certify that, within **thirty (30) days** of termination, any Railroad Data held by us has been destroyed, and that we hold none in normal operation. The only records we retain are the contractual and commercial documents in 5.2, which contain no Railroad operating data.

**Certified by:** ____________________  **Date:** __________

---

## Part 6 — Transition assistance delivered

Per D07 §15.6, 90 days at no charge. Record what was actually provided.

| # | Assistance | Provided | Date |
|---|---|---|---|
| 1 | Data export and verification | ☐ | |
| 2 | Export format documentation | ☐ | |
| 3 | Walkthrough of the export to Customer personnel | ☐ | |
| 4 | Final configuration statement (state of the platform at termination) | ☐ | |
| 5 | Support during migration to a successor system | ☐ | |
| 6 | Knowledge transfer sessions (up to 3) | ☐ | |

**Additional assistance requested beyond the 90 days:** __________ (billable at A2 §5.5)

---

## Part 7 — Outstanding matters

| # | Matter | Status | Owner |
|---|---|---|---|
| 1 | Final invoice | | |
| 2 | Escrow release required? | ☐ No ☐ Yes — per D13 §4 | |
| 3 | Certification registry update (revoke active certificates) | | |
| 4 | Equipment return (if any) | | |
| 5 | Remaining data on backup media | | |

---

## Part 8 — Signatures

**AxiomDynamics LLC**

Name: ____________________  Title: ____________________  Signature: ____________________  Date: __________

**Customer**

Name: ____________________  Title: ____________________  Signature: ____________________  Date: __________

**Customer confirms:** the export in Part 2 has been received and verified, the reconciliation in Part 4 is accepted, and the transition assistance in Part 6 has been delivered.

☐ Confirmed  ☐ Confirmed with reservations — state: __________

---

*Form F13. Uncontrolled when printed. Signed only when the export reconciles.*
