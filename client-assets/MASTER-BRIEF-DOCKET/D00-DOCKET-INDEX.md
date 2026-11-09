# AxiomDynamics — Master Brief Docket
## Docket Index & Document Map

**Classification:** Client-facing. Reviewed by both parties' counsel.
**Purpose:** a single, uniform set of documents that defines the entire relationship between AxiomDynamics and the Railroad — from technical architecture through pilot execution through multi-year licensing — so that legal, IT, safety and procurement are all reading the same instrument.

**The principle behind this docket:** one service, one set of terms, no parallel side-letters. Every document in here must reconcile with every other. Where two documents could conflict, the precedence clause in D02 governs. This exists to close the single most common loophole in rail technology contracts: a technical annex that promises something the master agreement disclaims.

---

## Part I — The relationship, in one sequence

```
PREFACE / DELIVERABLES CHECKLIST  (D01)
        ↓
BLUEPRINT OF THE BUILD  (B01–B05)
  flow map · infographic · tech stack · architecture
        ↓
SELF-DEPLOYMENT SOP  (C01)
  granular steps for the Railroad's own IT team
        ↓
CERTIFICATION & ROLE-BASED ASSESSMENT  (C02)
  who is trained, what they must prove, how they are certified
        ↓
MASTER PILOT AGREEMENT  (D02)
  the entry contract — scoped, time-boxed, reversible
        ↓
MASTER LICENSING & LIABILITY  (D08)
  what a licence is, what it costs, who bears what risk
        ↓
PILOT → YoY LICENSING ROLLOVER  (D05)
  how pilot converts to production without renegotiation
        ↓
TECH SUPPORT & RELEASE GOVERNANCE  (D06)
  updates, patching, CVE response, version policy
        ↓
COMPREHENSIVE MASTER CONTRACT  (D07)
  federal guidelines, data security, all limitations
```

---

## Part II — Document register

### A. Commercial model

| ID | Document | Status | Purpose |
|---|---|---|---|
| **A1** | ROI Model (`A1-ROI-MODEL/`) | **Built** | Five-sheet Excel business case. Yellow cells are the only inputs. Two pricing axes: per-axle licence + per-site platform fee. |
| **A2** | Rate Card & Band Definitions | Not built | The price list as a standalone citable annex. Needed because pricing currently lives inside A1 and D08, and a contract must cite one authoritative schedule. |

### B. Build blueprint — for the Railroad's internal IT

| ID | Document | Status | Purpose |
|---|---|---|---|
| **B01** | System Blueprint & Architecture | **Built** | Component inventory, data flow, disposition ledger requirements, failure modes, and the gap list where code differs from production. |
| **B02** | Flow Map | Not built | Visual: detector → edge → inference → reviewer → disposition → audit log. (Text flow is in B01 §3.) |
| **B03** | Infographic (one page) | Not built | One-page visual for executives who will not read B01. |
| **B04** | Technology Stack Disclosure | **Built** | Complete dependency register with licence types. One non-stdlib dependency (numpy). Verified against code. |
| **B05** | Data Flow & Residency Statement | **Built** | Definitively answers the air-gap question: zero outbound, verified against code. |

### C. Deployment & people

| ID | Document | Status | Purpose |
|---|---|---|---|
| **C01** | DIY Self-Deployment SOP | Not built | Granular, numbered, prerequisite-to-verification steps. Assumes a competent Linux admin, no prior rail-domain knowledge. |
| **C02** | Certification & Role-Based Assessment | Not built | Role definitions (operator, reviewer, admin, safety officer), competency matrix, assessment method, certification validity and revocation. |

### D. Legal — the contract stack

| ID | Document | Status | Purpose |
|---|---|---|---|
| **D01** | Preface & Master Deliverables Checklist | Not built | Front matter: what this docket is, what it is not, and the signed-off checklist. **Must be completed at Final Build before anything else is executed.** |
| **D02** | Master Pilot Agreement | **Built** | The entry contract. Scope, term, fees, evaluation criteria, warranties, liability cap, indemnities, termination. **Fees illustrative — confirm against A2 before signature.** |
| **D03** | Master Services Agreement (MSA) | Not built | The umbrella. Survives individual orders; governs all future statements of work. |
| **D04** | Statement of Work templates (SOW-1…n) | Not built | Executable per-deployment orders under the MSA. |
| **D05** | Pilot → YoY Licensing Rollover Agreement | Not built | The conversion mechanics: what happens on day 366, price protection, credit for pilot fees, conversion deadline, and what happens if the Railroad declines to convert. |
| **D06** | Technical Support, SLA & Update Governance | Not built | Response times, severity tiers, patching cadence, EOL policy, and **who pays for what when a patch is required for a defect we introduced.** |
| **D07** | Comprehensive Master Contract | Not built | Federal guidelines, data security, indemnities, limitation of liability, insurance, export control, audit rights, dispute resolution. |
| **D08** | Master Licensing & Liability | **Built (needs legal pass)** | Licensing structure, tier bands, performance component, and the liability split. Currently written commercially — must be converted to contract-grade language. |
| **D09** | Data Processing & Security Addendum (DPA) | Not built | The security schedule. Standalone because IT security review runs on a separate clock from procurement. |
| **D10** | Subprocessor & Third-Party Component Register | Not built | Every third party touching Railroad data. Pairs with B04. |
| **D11** | Mutual NDA | **Built** | Needed *before* D02. Often overlooked and always needed first. |
| **D12** | Regulatory Status & Safety-Critical Function Statement | **Built** | Single annex stating this is not a certified safety appliance, is not a substitute for required inspection, and relieves the Railroad of no regulatory obligation. Identical language across B01, C02, D02, D07, D08. See §III.1. |
| **D13** | IP Ownership & Escrow Schedule | **Built** | Definitive statement of what transfers and when. Records the five-year retention decision. Escrow releases the **running version only**, insolvency-triggered, operability never ownership. Includes contributor assignment requirement. |
| **D14** | Operating Model & Liability Boundary | **Built** | Who installs, operates, supports and staffs. Separates operational liability (largely removed by responsible self-install) from product liability (retained regardless). Sets representational discipline. |

---

## Part III — Loopholes identified, and current status

These are the gaps that most often go wrong in rail technology contracts specifically. Status markers show which are now closed by a built document and which remain open work.

### 1. The safety-critical disclaimer paradox — the biggest one

**Status: CLOSED** — D12 built. The decision-support framing is now fixed in D12 §§1–2, and D12 §9 makes it controlling over every other document.

Our claim is that we prevent derailments. Our inevitable limitation-of-liability clause will say we do not guarantee detection. **Put together, those two statements are a contradiction that a plaintiff's lawyer will find in ten minutes.**

The resolution is not to weaken either. It is to define the product precisely: AxiomDynamics is a **decision-support system** that presents a ranked, physics-derived risk assessment to a **qualified human reviewer**. The Railroad retains the operating decision. That framing must be *identical* in B01, C02, D02, D07 and D08 — same words, same scope. If the technical annex calls it a "detection system" and the contract calls it "decision support," we have manufactured our own liability.

**Add: D12 — Regulatory Status & Safety-Critical Function Statement.** A single annex that states, unambiguously, that this is not a certified safety appliance, is not a substitute for FRA-required inspection, and does not relieve the Railroad of any regulatory obligation. This protects both parties and is the document that makes the disclaimer credible rather than self-serving.

### 2. Data ownership vs. model improvement

**Status: CLOSED** — D13 §3 separates ownership explicitly. Default position is no cross-customer learning, which under AD-1 is structurally true rather than merely promised.

The standard clause — "Railroad owns its data" — is insufficient. The Railroad will ask: *if you train on our data, and the model improves, do we own the improvement? Do our competitors benefit?* Left unanswered, this stalls the deal at legal review every time.

**Add to D07/D09:** explicit separation of (a) Railroad's raw and derived operating data — owned by Railroad; (b) AxiomDynamics' models, weights, rules and source — owned by AxiomDynamics, including improvements derived from Railroad data; (c) a licence back to the Railroad for its own data in usable form on termination. Also state plainly whether cross-customer learning occurs — and if it does, that it is aggregated and non-attributable.

### 3. The "who pays for the false positive" gap

A false stop on a Class I main line costs train-hours, crew-hours, and network knock-on. Our marketing claims <0.1% false positives. **Nothing in the current documents says who bears the cost when we are wrong.** A railroad's counsel will ask this in the first meeting. If we have no answer, they will assume we bear it.

**Add to D06/D08:** a defined false-positive cost regime — for example, a service credit schedule tied to verified false-positive volume, capped, and explicitly excluding consequential damages. This converts an unbounded risk into a bounded, priced one.

### 4. Detector data rights and the integration dependency

We integrate with the Railroad's existing wayside detectors. Who warrants that the detector data is accurate? Who is liable if the HBD feeding us is miscalibrated and we therefore miss a defect?

**Add to D07:** a clear allocation. The Railroad warrants that detector hardware is maintained per its own standards and AAR recommended practice; AxiomDynamics warrants its processing of that data. **Neither party warrants the other's equipment.** Silence here is dangerous in both directions.

### 5. Rollover cliff — the commercial trap in D05

If the pilot converts on day 366 at full production price with no credit for pilot fees, the Railroad's internal ROI calculation changes shape at conversion and the deal dies at the CFO's desk, not the lawyer's. **D05 must specify: pilot fee credit, price protection for the first production term, a conversion window, and a defined outcome if they decline** — including whether they keep any data or reports produced during the pilot.

### 6. Certification liability — an unnoticed exposure

C02 certifies the Railroad's personnel. **If we certify someone and they then make a consequential error, are we liable for the certification?** This is a real and commonly-missed exposure in any product that trains its customer's staff. D07 must state that certification evidences competency against our curriculum, not a guarantee of individual performance, and that the Railroad retains employment and supervision responsibility.

### 7. The air-gap representation problem

We tell customers "on-premise, air-gap capable." If the product requires *any* outbound network call — licence check, telemetry, update ping — that representation is false, and it is the kind of false that surfaces during a security audit in month three.

**B05 must be written by someone looking at the actual code, not the marketing.** Then D07 must match B05 exactly. If we need a licence server, say so and design the offline activation path; do not claim air-gap and then require a phone-home.

### 8. Missing: cyber incident notification

Rail is now explicitly in scope for transportation-sector cyber risk. D09 must include a **breach notification window** (typically 72 hours), the notification channel, and what constitutes a reportable incident. Absent this, the Railroad's CISO will block the deployment regardless of what procurement agreed.

### 9. Missing: personnel security and background checks

Railroad IT will ask whether our engineers have background checks, and whether they will accept the Railroad's. Especially relevant given federal hazmat and security-sensitive rail requirements.

### 10. Missing: export control and sanctions

Even a domestic-only deployment can raise export-control questions if any component or engineer is foreign-sourced. Cheap to address in D07, expensive to discover later.

### 11. Missing: escrow

**Status: CLOSED** — D13 §4. Insolvency-triggered, running-version deposit, operability never ownership.

If AxiomDynamics ceases to exist, can the Railroad keep operating? A **source code escrow** agreement (triggered on insolvency or cessation of support) is the standard answer and is often the clause that lets a sole-source vendor be approved at all. Given that this is a company selling to organisations that plan in decades, expect this question.

### 12. Missing: transition and exit assistance

What does the Railroad get on termination — data export format, a defined assistance period, and a prohibition on our retaining copies. Must be specified, not implied.

---

## Part IV — Precedence and construction

To prevent the loophole where a technical annex contradicts the master contract:

1. **D07 Comprehensive Master Contract** governs generally.
2. **D02 Master Pilot Agreement** governs during the pilot term, where it conflicts with D07.
3. **D04 SOW** governs scope of work and deliverables for that specific order.
4. **A2 Rate Card** governs price.
5. **B-series technical annexes** are descriptive and do not create warranties unless D07 expressly incorporates them.
6. Where a B-series document describes a capability that D07 disclaims, **the disclaimer governs and the annex must be corrected** — this is a drafting error to be fixed, not a gap to be argued.

That rule 6 is the one that keeps this docket honest over time.

---

## Part V — Build status at a glance

**Built (10):** A1 ROI model · B01 blueprint · B04 tech stack · B05 data flow · D02 pilot agreement · D08 licensing · D11 NDA · D12 regulatory status · D13 IP & escrow · D14 operating model.

**Open loopholes still requiring a document:** the false-positive cost regime (D06), detector data warranty allocation (D07), cyber incident notification (D09), personnel security (D07), export control (D07), transition assistance (D07), certification liability (D07), and rollover cliff (D05).

**Next by value:** C01 deployment SOP (the self-install model depends on it) · D07 master contract (closes the most remaining loopholes) · C02 certification (the Canadian argument rests on it) · A2 rate card (D02 fees are illustrative until it exists).

**Deferred by decision:** the pilot-proposal narrative — superseded by D02 as a legal instrument.

**Internal, moved to `assets/`:** carrier dossiers, library reconciliation, IP strategy.

**Architectural decisions locked (B01):** fully on-premise edge, zero outbound network; local accounts plus signed certification registry; append-only disposition ledger.

**Commercial decision locked (D13):** AxiomDynamics retains all IP; escrow grants operability only on insolvency.

---

*This docket index is a working structure, not a legal opinion. Every document in Part II under D must be reviewed by qualified counsel in the relevant jurisdiction before execution. Nothing here constitutes legal advice.*
