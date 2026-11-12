# F08 — Reviewer Certification Application

**AxiomDynamics LLC** · Form F08 · Version 1.0 · Effective ____________ · **Retain 7 years (plus certification life)**

**Purpose:** to apply for certification of a Customer employee to record advisory dispositions in the Platform.

**Governing reference:** C02 (Certification & Role-Based Assessment).

> **Why this form exists:** **since 2026-11-11 a certification ID can no longer be self-asserted at entry** — a disposition requires a local account bound to a live certification record, and the reviewer identity on the row comes from the authenticated session (B01 §7 item 1; D09 §4.4). What this form still does, and what the code does not, is establish **who the person behind that credential is**: issuing the credential, keeping custody of it, and withdrawing it on a mover or leaver. Entry additionally does not require an **attestation**, only a live session, so an attested row remains the reviewer's choice. **This form therefore stays the authoritative record of who is certified and who holds which credential**, signed, filed, checked against the Platform's user list, and the document from which an account and a registry key are issued. That manual control is what substitutes for the personnel control software cannot provide. **Since 2026-11-11 the process it feeds is written down:** D09 §8.4 is the joiner/mover/leaver procedure — this form is its step one, `tools/issue_reviewer_key.py` is step two, and the custody log (§8.4.6) records the `key_id` this form authorises. F08 is also what the quarterly reconciliation in §8.4.8 checks the live registry against, so a reviewer on the Platform without a signed F08 is a credential nobody authorised.

---

## Part 1 — Candidate

| | |
|---|---|
| Customer | |
| Site | |
| Candidate full name | |
| Employee ID | |
| Job title | |
| Department | |
| **Role applied for** | ☐ Operator ☐ Reviewer ☐ Administrator ☐ Safety Officer |
| Application date | |
| Nominated by (Customer sponsor) | |

---

## Part 2 — Eligibility (completed by the Customer sponsor)

**Reviewers must meet all of the following.** Confirm each:

☐ **At least 12 months of railroad operating, mechanical, or inspection experience** — years: ______
☐ Currently employed by the Customer in a role that touches rolling stock, track, or inspection
☐ Not under any disciplinary restriction affecting safety-critical duties
☐ Available to review advisories within the Customer's defined response window
☐ Willing to record dispositions in writing, including where the Platform is judged wrong

**Administrators must meet all of the following:**

☐ **At least 2 years of hands-on Linux system administration**
☐ Able to manage the host, the database, backups, and the NTP configuration
☐ Holds the Customer's internal authority to operate the Platform host

**Operators (read-only) require:**

☐ A business need to view advisories
☐ No disciplinary restriction

---

## Part 3 — Curriculum completion

| Module | Completed | Date | Score |
|---|---|---|---|
| Role and boundaries of a Reviewer (C02 §2) | ☐ | | |
| Reading an advisory: what the Platform computes | ☐ | | |
| The physics behind the ranked risk score | ☐ | | |
| Disposition discipline: recording reject, accept, defer | ☐ | | |
| What a Reviewer must **never** do (operating decisions, inspection substitution) | ☐ | | |
| Record keeping and the append-only ledger | ☐ | | |
| Escalation and the support boundary | ☐ | | |

**Assessment result:** ______ %  **Pass threshold:** **80%** (C02 §3.2)

---

## Part 4 — Assessment record

| | |
|---|---|
| Assessed by (AxiomDynamics) | |
| Assessment date | |
| Format | ☐ Written ☐ Practical ☐ Both |
| Result | ☐ **Pass** ☐ **Fail** — retake permitted after ______ |

---

## Part 5 — Critical acknowledgements

**The candidate must initial each line.** These are not boilerplate — each one is a specific boundary the candidate is being trusted with.

| Initial | Acknowledgement |
|---|---|
| ____ | I understand the Platform is a **decision-support tool**, not a certified safety appliance (D12). |
| ____ | I understand the Platform does **not** satisfy any WDBD or other regulatory inspection requirement (D12 §3). |
| ____ | I understand that **I**, not AxiomDynamics, make the operating decision. The Platform ranks risk; I decide what happens to the train. |
| ____ | I will **never** rely on the Platform as a substitute for a required inspection. |
| ____ | I will record a disposition for **every** advisory assigned to me, including where I judge the Platform to be wrong. |
| ____ | I will not ask AxiomDynamics personnel for operating advice, and I understand they will decline to give it (D06 §1.4). |
| ____ | I will record dispositions under my own name only, and will not share my credentials. |
| ____ | I understand my certification is **valid for three years**, with renewal on the three-year cycle (C02 §4.1). |
| ____ | I understand my certification may be **revoked** by the Customer or suspended by AxiomDynamics for misuse (Part 8). |

---

## Part 6 — Certification issued

| | |
|---|---|
| **Certificate number** | **CRT-______** |
| Role certified | |
| Issued date | |
| **Valid until** (3 years) | |
| **Renewal due** (year 2) | |
| Issued by (AxiomDynamics) | |

**Registry entry made:** ☐ Yes — date: __________  **Platform user account created:** ☐ Yes — username: __________

---

## Part 7 — What certification does and does not mean

**It means:** the holder completed the curriculum and passed an assessment against it. That is a statement about training.

**It does not mean:** that the holder will never make an error; that the holder is competent in every situation; that AxiomDynamics supervises or directs the holder's work; or that AxiomDynamics accepts liability for the holder's acts or omissions.

**The Customer remains solely responsible for the employment, supervision, and performance of its personnel** (D07 §16). Certification evidences curriculum completion and creates no liability for a Certified Reviewer's act (D07 §16).

---

## Part 8 — Revocation

Certification is revoked or suspended on:

1. Termination of the holder's employment with the Customer
2. Misuse of credentials or recording a disposition under another person's name
3. Recording a disposition for an advisory the holder did not review
4. Failure to renew
5. Written request of the Customer's Safety Officer

**The Customer must notify AxiomDynamics of any revocation within 10 Business Days** so the registry is updated (D09 §8.2). **Failure to notify is a Customer obligation under D03 §6**, and it leaves an active credential in a system for a person who no longer holds it.

**Revocation record:**

| | |
|---|---|
| Certificate revoked | CRT-______ |
| Reason | |
| Effective date | |
| Notified by | |
| Registry updated on | |

---

## Part 9 — Signatures

**Candidate** — I confirm the acknowledgements in Part 5, and that the information in Parts 1–2 is accurate.

Name: ____________________  Signature: ____________________  Date: __________

**Customer sponsor** — I confirm the eligibility statements in Part 2, and that this person is authorised to review advisories on the Customer's behalf.

Name: ____________________  Title: ____________________  Signature: ____________________  Date: __________

**AxiomDynamics** — certification issued as recorded in Part 6.

Name: ____________________  Title: ____________________  Signature: ____________________  Date: __________

---

## Part 10 — Renewal record

| Cycle | Assessment date | Score | Renewed until | Signed |
|---|---|---|---|---|
| Year 2 renewal | | | | |
| Year 3 (re-certification) | | | | |

---

*Form F08. Uncontrolled when printed. The certification registry is the authoritative record; this form is its source document.*
