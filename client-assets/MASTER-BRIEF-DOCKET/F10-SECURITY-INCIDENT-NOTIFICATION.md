# F10 — Security Incident Notification

**AxiomDynamics LLC** · Form F10 · Version 1.0 · Effective ____________ · **Retain 7 years**

**Purpose:** the notification record required by D09 §6 when a reportable security incident occurs.

**Notification windows (D09 §6):**
- **Supplier → Customer: 72 hours** from confirmation
- **Customer → Supplier: 24 hours** from discovery of a Platform vulnerability

> **72 hours is not a target.** It is the outer limit. In practice the first notification should go within 24 hours, even if it says only "we have confirmed an incident, we do not yet know the scope, here is who is handling it." A partial notification inside the window is worth far more than a complete one outside it — to the Customer's CISO, and to us if the incident is later examined.

---

## Part 1 — Incident identification

| | |
|---|---|
| Incident reference | INC-______ |
| Reporting party | ☐ AxiomDynamics ☐ Customer |
| Date and time discovered | |
| Date and time confirmed | |
| **Notification due by** (confirmed + 72h or 24h) | |
| **Notification sent at** | |
| Within required window? | ☐ Yes ☐ No — reason: __________ |

---

## Part 2 — Classification

**Reportable under D09 §6.2?** ☐ Yes ☐ No

If no, state the basis:

☐ Routine failed login attempts ☐ Scheduled maintenance or patch ☐ Unweaponised vulnerability disclosure with no patch available ☐ Other: __________

**Severity:** ☐ Critical ☐ High ☐ Medium ☐ Low

**Category:**

☐ Unauthorised access to the Platform or Railroad Data
☐ Loss or theft of a device containing Platform data or credentials
☐ Malicious code in the Platform or dependency chain
☐ Third-party disclosure of a vulnerability affecting a production deployment
☐ Breach of Supplier systems that could expose Railroad Data
☐ Other: __________

---

## Part 3 — What happened

**3.1 Description in plain words:**

________________________________________________________________

**3.2 Systems affected:**

☐ Platform application ☐ Platform database ☐ Host operating system ☐ Dependency
☐ Supplier systems ☐ Customer systems ☐ Network ☐ Other: __________

**3.3 Sites affected:** ____________________

**3.4 Estimated records or systems involved:** __________

**3.5 Is Railroad Data confirmed accessed, or only potentially accessible?**

☐ Confirmed accessed ☐ Potentially accessible ☐ Not accessible ☐ Unknown

> **Answer "unknown" if it is unknown.** An early "unknown" that later resolves to "not accessed" is a good outcome. An early "not accessed" that later resolves to "accessed" destroys credibility at exactly the moment credibility is the only asset left.

---

## Part 4 — Containment

| | |
|---|---|
| Containment measures taken | |
| Date and time contained | |
| Is the incident ongoing? | ☐ No ☐ Yes — current state: __________ |
| Workaround available to Customer? | ☐ No ☐ Yes — describe: __________ |
| Patch required? | ☐ No ☐ Yes — target release date: __________ |

---

## Part 5 — Notification content (D09 §6.1 required elements)

Confirm each required element is included:

☐ Description of the incident and what was affected
☐ Estimated number of records or systems involved
☐ Containment measures taken
☐ Root cause (if known) — ☐ Known ☐ Not yet determined
☐ Measures to prevent recurrence

---

## Part 6 — Regulatory notification

**D09 §6.5:** the **Customer** is responsible for notifying regulators and affected individuals. We assist by providing information but do not make regulatory notifications on the Customer's behalf.

| | |
|---|---|
| Does the Customer consider this reportable to a regulator? | ☐ Yes ☐ No ☐ Under assessment |
| Regulator(s) identified by Customer | |
| Customer's notification deadline (if any) | |
| Information we will provide to support it | |
| Date provided | |

**Jurisdictional note:** US state breach notification laws and Canada's PIPEDA have different triggers and deadlines. The Customer's legal team determines applicability. We provide facts, not legal advice — that includes not advising on whether a notification is required.

---

## Part 7 — Post-incident review (D09 §6.4)

| | |
|---|---|
| Root-cause analysis due | Within 30 days of containment: __________ |
| RCA delivered on | |
| Joint review scheduled | Within 10 Business Days of RCA: __________ |
| Joint review attendees | |
| Corrective actions agreed | |

---

## Part 8 — Timeline log

| Time | Event | By |
|---|---|---|
| | Incident occurred (estimated) | |
| | Discovered | |
| | Confirmed | |
| | Notified Customer | |
| | Contained | |
| | RCA delivered | |
| | Closed | |

---

## Part 9 — Signatures

**Reported by (AxiomDynamics)**

Name: ____________________  Title: ____________________  Signature: ____________________  Date/Time: __________

**Received by (Customer)**

Name: ____________________  Title: ____________________  Signature: ____________________  Date/Time: __________

**Incident closed:** ☐ Yes — date: __________  **Closed by:** __________

---

## Part 10 — Standing contact list

*Kept current. An incident notification sent to a departed employee's address is a notification that did not happen.*

| Role | Name | Email | Phone (24h) |
|---|---|---|---|
| AxiomDynamics security contact | | | |
| AxiomDynamics Principal Architect | | | |
| Customer IT Director | | | |
| Customer CISO / security | | | |
| Customer Pilot Sponsor | | | |

**Last verified:** __________

---

*Form F10. Uncontrolled when printed. 72 hours is the limit, not the target.*
