# D01 — Preface & Master Deliverables Checklist

**Docket position:** D01. Front matter. **Completed at Final Build, before anything is executed.**

**Classification:** Client-facing.

---

## Part 1 — What this docket is

This is the complete documentary record of what AxiomDynamics offers, what it does not offer, what it costs, and who bears which risk. It is written so that four different readers can each find what they need without reading all of it:

| Reader | Start here | Then |
|---|---|---|
| **Chief Engineer / operations** | B01 (what it does) | D12 (what it is not), C02 (who runs it) |
| **IT / security** | B05 (data flow), C01 (deployment) | D09 (security schedule), B04 (dependencies) |
| **Procurement / finance** | A2 (rate card) | D02 (pilot terms), D05 (rollover), F05 (payment) |
| **Legal** | D07 (master contract) | D03 (MSA), D13 (IP), D14 (liability boundary) |

**Every document reconciles with every other.** Where two could conflict, the precedence order in D00 Part IV governs. That structure exists to close the single most common failure in rail technology contracting: a technical annex that promises something the master agreement disclaims.

---

## Part 2 — What this docket is not

State these plainly, because each one is a misunderstanding that would otherwise surface in month three.

1. **It is not a claim of certification.** The Platform is not a certified safety appliance and does not satisfy any WDBD, HBD, or other regulatory inspection requirement (D12 §3).
2. **It is not a guarantee of detection.** No document here promises that a particular defect will be found (D02 §7.2).
3. **It is not legal advice.** Every document requires review by qualified counsel in the governing jurisdiction before execution.
4. **It is not a proposal to integrate.** The Platform is a separate overlay. It does not read from or write to any control, signal, or protection system (D02 §6).
5. **It is not a fixed-price commitment beyond what is signed.** Fees are illustrative until an A2-priced Order is executed.
6. **It is not complete in the sense of finished forever.** It is a maintained instrument with version control (F00 Part 4).

---

## Part 3 — The documents, and what each is for

### Commercial
| ID | Document | One-line purpose |
|---|---|---|
| A1 | ROI Model | The business case, with the customer's own numbers |
| A2 | Rate Card | The authoritative price schedule |

### Technical — for the Customer's IT
| ID | Document | One-line purpose |
|---|---|---|
| B01 | System Blueprint | Component inventory, data flow, gap register |
| B04 | Technology Stack | Every dependency and its licence |
| B05 | Data Flow & Residency | The code-verified air-gap statement |

### Deployment and people
| ID | Document | One-line purpose |
|---|---|---|
| C01 | Self-Deployment SOP | The customer installs it themselves, step by step |
| C02 | Certification & Roles | Who is trained, what they must prove |

### Contracts
| ID | Document | One-line purpose |
|---|---|---|
| D02 | Master Pilot Agreement | The entry contract |
| D03 | Master Services Agreement | The umbrella that survives orders |
| D04 | SOW Templates | The executable orders |
| D05 | Rollover Agreement | How the pilot becomes production |
| D06 | Support, SLA & Updates | Response times, patching, false-positive credits |
| D07 | Comprehensive Master Contract | The full terms |
| D08 | Licensing & Liability | Licensing structure and the risk split |
| D09 | DPA | The security schedule |
| D10 | Component Register | Every third party that touches data or ships in the Platform (currently: none, and numpy) |
| D11 | Mutual NDA | Signed first, always |
| D12 | Regulatory Status | What this is not |
| D13 | IP & Escrow | What transfers and when |
| D14 | Operating Model & Liability Boundary | Who does what |

### Forms
| ID | Form | One-line purpose |
|---|---|---|
| F00 | Forms Register & Documentation Policy | The index and the rules |
| F01 | Site Readiness Questionnaire | Can this site support it |
| F02 | Configuration Attestation | Starts the pilot clock |
| F03 | Change Order | The only way scope changes |
| F04 | Travel Pre-Approval | Before any billable travel |
| F05 | Payment Terms | What is paid, when |
| F06 | Deliverable Acceptance | Delivery, acceptance, deemed acceptance |
| F07 | Travel & Expense Claim | Reimbursement at cost |
| F08 | Reviewer Certification Application | Who may record dispositions |
| F09 | Advisory Disposition Record | The human decision, recorded |
| F10 | Security Incident Notification | 72-hour obligation |
| F11 | Site Visit Report | What we did, and did not do |
| F12 | Formal Notice | Termination, breach, elections |
| F13 | Data Export & Transition Certificate | What the customer gets when it ends |

---

## Part 4 — Pre-execution checklist

**Every line must be complete before the first document is signed by a customer.** This checklist is the gate.

### Entity and authority
- ☐ Legal entity formed; certificate of formation on file
- ☐ EIN issued
- ☐ Operating agreement executed
- ☐ Signatory has documented authority to bind the entity
- ☐ Bank account open; no commingling
- ☐ Insurance bound: CGL, Technology E&O, Cyber (D03 §9)
- ☐ Certificates of insurance available on request
- ☐ State filings current; good standing certificate pulled (D01 Part 4 above)

### Commercial
- ☐ A2 rate card finalised and dated
- ☐ A1 ROI model recalculated against final A2 figures
- ☐ Pilot fee confirmed against A2 §5.1
- ☐ Travel policy confirmed (A2 §5.3, F04, F07)
- ☐ Payment terms confirmed with the customer's AP (F05)
- ☐ Purchase order process understood

### Contract integrity
- ☐ D02 fees match A2 §5.1 exactly
- ☐ D05 rollover arithmetic matches A2 §9
- ☐ D08 tier figures match A2 §3
- ☐ D06 response times confirmed against actual capacity
- ☐ D07 insurance limits match the policies actually bound (see D03 §9 note)
- ☐ All incorporated-document references resolve

### Technical honesty
- ☐ B01 §7 gap register current
- ☐ D09 §4.4 disclosed gaps current
- ☐ **Append-only ledger implemented** — if not, F09 Part 7 disclosure is present and D09 §4.4 discloses it
- ☐ **Signed certification registry implemented** — if not, F08 Part 1 manual control is in force
- ☐ B05 outbound-call statement re-verified against the deployed build
- ☐ No annex claims a capability the code does not have

### The final gate
- ☐ **Read D00 Part III, all twelve loopholes, and confirm each closure is still true of the current build**
- ☐ **Read D00 Part IV rules 6 and 9 — confirm A2 governs every price figure, and confirm no annex describes a capability the disclaimer disclaims**
- ☐ Counsel has reviewed D02, D03, D07, D09, D12, D13, D14

> **The last two checkboxes are the ones that stop a docket from becoming a liability.** Everything else is preparation. Those two are the honesty check, and they must be run again every time the build changes.

---

## Part 5 — Standing representations

These are true as at the Effective Date and are restated here so they appear in one place.

1. The Platform contains no outbound network mechanism (verified against code, B05; stated contractually in D09 §3.2 and D07 §7.1).
2. The only third-party runtime dependency is numpy, BSD-3-Clause (B04).
3. No subprocessors process Railroad Data (D09 §7.1).
4. AxiomDynamics retains all IP in the Platform, models, and documentation (D13).
5. Escrow grants operability on insolvency, never ownership (D13 §4).
6. The Platform is a decision-support tool, not a certified safety appliance (D12).
7. Installation is performed by the Customer (D14 §3).
8. Known gaps are disclosed in D09 §4.4 and B01 §7, not omitted.

**If any of these becomes untrue, the docket is amended before the next customer conversation.** A standing representation that has quietly expired is worse than no representation at all.

---

## Part 6 — Signature on this preface

This preface is not a contract. It records that the parties have read the docket structure and understand what they are being offered.

**AxiomDynamics LLC:** ____________________  **Date:** __________

**Customer (acknowledging receipt of the docket):** ____________________  **Date:** __________

---

*Preface. Completed at Final Build. Not legal advice.*
