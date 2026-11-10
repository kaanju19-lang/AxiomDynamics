# AxiomDynamics — Master Brief Docket
## Docket Index & Document Map

**Classification:** Client-facing. Reviewed by both parties' counsel.
**Purpose:** a single, uniform set of documents that defines the entire relationship between AxiomDynamics and the Railroad — from technical architecture through pilot execution through multi-year licensing — so that legal, IT, safety and procurement are all reading the same instrument.

**The principle behind this docket:** one service, one set of terms, no parallel side-letters. Every document in here must reconcile with every other. Where two documents could conflict, **the precedence ladder in Part IV of this document governs** — D02 contains no precedence clause of its own, and an index that points at a clause that does not exist is the same dangling-reference failure it exists to prevent. This exists to close the single most common loophole in rail technology contracts: a technical annex that promises something the master agreement disclaims.

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
| **A2** | Rate Card & Band Definitions | **Built** | The price list as a standalone citable annex. **Governs price across the entire docket** — where any other document's fee differs from A2, A2 wins. Includes worked calculations and the rollover arithmetic. |

### B. Build blueprint — for the Railroad's internal IT

| ID | Document | Status | Purpose |
|---|---|---|---|
| **B01** | System Blueprint & Architecture | **Built** | Component inventory, data flow, disposition ledger requirements, failure modes, and the gap list where code differs from production. |
| **B02** | Flow Map | Built (.md) | Visual: detector → edge → inference → reviewer → disposition → audit log. Solid = shipped; dotted = designed, not built. (Text flow is in B01 §3.) |
| **B03** | Infographic (one page) | Built (.html) | One-page visual for executives who will not read B01. Encodes the platform/human boundary as a break in the drawn line. |
| **B04** | Technology Stack Disclosure | **Built** | Complete dependency register with licence types. One non-stdlib dependency (numpy). Verified against code. |
| **B05** | Data Flow & Residency Statement | **Built** | Definitively answers the air-gap question: zero outbound, verified against code. |

### C. Deployment & people

| ID | Document | Status | Purpose |
|---|---|---|---|
| **C01** | DIY Self-Deployment SOP | **Built** | Granular, numbered, prerequisite-to-verification steps. Assumes a competent Linux admin, no prior rail-domain knowledge. |
| **C02** | Certification & Role-Based Assessment | **Built** | Role definitions (operator, reviewer, admin, safety officer), competency matrix, assessment method, certification validity and revocation. |

### D. Legal — the contract stack

| ID | Document | Status | Purpose |
|---|---|---|---|
| **D01** | Preface & Master Deliverables Checklist | **Built** | Front matter: what this docket is, what it is not, the pre-execution checklist, and the eight standing representations. **Completed at Final Build before anything else is executed.** |
| **D02** | Master Pilot Agreement | **Built** | The entry contract. Scope, term, fees, evaluation criteria, warranties, liability cap, indemnities, termination. Now includes **§§3.5–3.7** on travel, expenses and expansion-site pricing. Fees confirmed against A2 §5.1. |
| **D03** | Master Services Agreement (MSA) | **Built** | The umbrella. Signed once per customer, survives individual orders, governs ordering and change control. |
| **D04** | Statement of Work templates (SOW-1…5) | **Built** | Executable per-deployment orders: SOW-1 Pilot Implementation · SOW-2 Additional Site · SOW-3 Feasibility & Physics Assessment · SOW-4 Prototype Development · SOW-5 Professional Services. |
| **D05** | Pilot → YoY Licensing Rollover Agreement | **Built** | The conversion mechanics: what happens on day 366, price protection, credit for pilot fees, conversion deadline, and what happens if the Railroad declines to convert. |
| **D06** | Technical Support, SLA & Update Governance | **Built** | Response times, severity tiers, patching cadence, EOL policy, and the false-positive cost regime (quarterly service credits). |
| **D07** | Comprehensive Master Contract | **Built** | Federal guidelines, data security, indemnities, limitation of liability, insurance, export control, audit rights, dispute resolution. |
| **D08** | Master Licensing & Liability | **Built — but it is a commercial annex, not an instrument to sign** | Licensing structure, tier bands, workable corridor economics, performance component. D08 explains the money; **D07 and D02 are what a customer executes.** Where D08 and either of them differ, they govern and D08 is corrected. |
| **D09** | Data Processing & Security Addendum (DPA) | **Built** | The security schedule: data residency, security controls, incident notification (72h), retention, subprocessor register, audit rights. |
| **D10** | Subprocessor & Third-Party Component Register | **Built** | Zero subprocessors. One runtime dependency (numpy, BSD-3). Restates the supply-chain gaps. **Incorporated by reference in D02 §11, D07 §3.4, D13 §8 and B04 §7 — now exists.** |
| **D11** | Mutual NDA | **Built** | Needed *before* D02. Often overlooked and always needed first. |
| **D12** | Regulatory Status & Safety-Critical Function Statement | **Built** | Single annex stating this is not a certified safety appliance, is not a substitute for required inspection, and relieves the Railroad of no regulatory obligation. Identical language across B01, C02, D02, D07, D08. See §III.1. |
| **D13** | IP Ownership & Escrow Schedule | **Built** | Definitive statement of what transfers and when. Records the five-year retention decision. Escrow releases the **running version only**, insolvency-triggered, operability never ownership. Includes contributor assignment requirement. |
| **D14** | Operating Model & Liability Boundary | **Built** | Who installs, operates, supports and staffs. Separates operational liability (largely removed by responsible self-install) from product liability (retained regardless). Sets representational discipline. |

### E. Forms — the executable instruments

Contracts say what the rules are. **Forms are how the rules are actually applied, one event at a time.** Every form is one purpose, one signatory, one stated consequence for silence.

| ID | Form | Status | Purpose |
|---|---|---|---|
| **F00** | Forms Register & Documentation Policy | **Built** | The index, the seven documentation rules, and the rule that governs the others: *if no form exists for what you are about to do, create the form first.* Rule 7 separates a fill-in blank from an unmade decision. |
| **F01** | Site Readiness & Survey Questionnaire | **Built** | Pre-deployment site assessment: detector, compute, network, people, existing systems. |
| **F02** | Configuration Attestation | **Built** | The Customer's IT Director certifies the installation. **Establishes the Commissioning Date and starts the pilot clock.** The single most important form in the docket. |
| **F03** | Change Order | **Built** | The only mechanism by which scope, price or schedule may change on an executed Order. 8-hour tolerance for minor change. |
| **F04** | Travel Pre-Approval Request | **Built** | Written approval before any billable travel. Records what we will and will not do on site. |
| **F05** | Payment Terms Schedule | **Built** | What is paid, when, and how. Includes the invoicing-discipline rules and the non-suspension commitment. |
| **F06** | Deliverable Acceptance | **Built** | Acceptance, acceptance-with-notes, or specific non-conformity. **Silence past 10 Business Days is acceptance.** |
| **F07** | Travel & Expense Claim | **Built** | Reimbursement at actual cost, no markup, with cap reconciliation. |
| **F08** | Reviewer Certification Application | **Built** | Application, assessment, certification, and revocation. **Currently the authoritative certification record** until the signed registry is built. |
| **F09** | Advisory Disposition Record | **Built** | The human decision, recorded. The most legally significant record the Platform produces. Discloses the append-only gap in Part 7. |
| **F10** | Security Incident Notification | **Built** | 72-hour Supplier notice, 24-hour Customer notice, RCA, and regulatory hand-off. |
| **F11** | Site Visit Report | **Built** | What we observed, **and what we declined to do.** Part 4 records every boundary event. |
| **F12** | Formal Notice | **Built** | Termination, breach, cure, non-renewal, conversion election. Delivery method determines effectiveness. |
| **F13** | Data Export & Transition Certificate | **Built** | What the Customer gets when it ends, in specific files, with reconciliation. |

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

**Status: CLOSED** — D06 §4 defines a quarterly service credit schedule tied to measured false-positive rate, capped at the platform fee, excluding detector-data causes and consequential damages.

A false stop on a Class I main line costs train-hours, crew-hours, and network knock-on. **Nothing in the current documents says who bears the cost when we are wrong.** A railroad's counsel will ask this in the first meeting. If we have no answer, they will assume we bear it.

> **Note on the false-positive figure.** Earlier internal drafts cited "<0.1% false positives" as a marketing claim. **That figure was never measured and has been withdrawn from the client-facing docket** — D06 §4 now sets a measurement regime with no target, and A2 states no target. Claiming a rate before measuring it, in the same docket that promises a credit when the rate is high, is the contradiction a plaintiff would build a case on.

**Add to D06/D08:** a defined false-positive cost regime — for example, a service credit schedule tied to verified false-positive volume, capped, and explicitly excluding consequential damages. This converts an unbounded risk into a bounded, priced one.

### 4. Detector data rights and the integration dependency

**Status: CLOSED** — D07 §6 allocates the warranty in three parts: Railroad warrants its detector hardware; Supplier warrants its processing; neither warrants the other's domain. The Configuration Attestation plus detector maintenance records plus processing logs determine which domain a failure falls in.

We integrate with the Railroad's existing wayside detectors. Who warrants that the detector data is accurate? Who is liable if the HBD feeding us is miscalibrated and we therefore miss a defect?

**Add to D07:** a clear allocation. The Railroad warrants that detector hardware is maintained per its own standards and AAR recommended practice; AxiomDynamics warrants its processing of that data. **Neither party warrants the other's equipment.** Silence here is dangerous in both directions.

### 5. Rollover cliff — the commercial trap in D05

**Status: CLOSED** — D05 built. 90-day conversion election window; 50% pilot licence credit ($90K); three-year price lock (Years 1–3 at 0% increase, Year 4+ capped at 5%/yr); defined exit if declined; Year 1 termination for convenience at 60 days with no penalty.

If the pilot converts on day 366 at full production price with no credit for pilot fees, the Railroad's internal ROI calculation changes shape at conversion and the deal dies at the CFO's desk, not the lawyer's. **D05 must specify: pilot fee credit, price protection for the first production term, a conversion window, and a defined outcome if they decline** — including whether they keep any data or reports produced during the pilot.

### 6. Certification liability — an unnoticed exposure

**Status: CLOSED** — D07 §16. Certification evidences completion of the curriculum and creates no liability for a Certified Reviewer's act or omission; the Railroad is solely responsible for its personnel.

C02 certifies the Railroad's personnel. **If we certify someone and they then make a consequential error, are we liable for the certification?** This is a real and commonly-missed exposure in any product that trains its customer's staff. D07 must state that certification evidences competency against our curriculum, not a guarantee of individual performance, and that the Railroad retains employment and supervision responsibility.

### 7. The air-gap representation problem

**Status: CLOSED** — B05 verified against code: zero outbound calls. D09 §3.2 and D07 §7.1 both state it contractually. All four supply-chain gaps (dependency pinning, hash verification, SBOM and signed release artefacts — see B04 §7 and D09 §4.4) are disclosed in D09 §4.4 rather than papered over.

We tell customers "on-premise, air-gap capable." If the product requires *any* outbound network call — licence check, telemetry, update ping — that representation is false, and it is the kind of false that surfaces during a security audit in month three.

**B05 must be written by someone looking at the actual code, not the marketing.** Then D07 must match B05 exactly. If we need a licence server, say so and design the offline activation path; do not claim air-gap and then require a phone-home.

### 8. Cyber incident notification

**Status: CLOSED** — D09 §6. 72-hour Supplier-to-Railroad notification, 24-hour Railroad-to-Supplier for discovered vulnerabilities, defined reportable incident, 30-day root-cause analysis, and joint review. D07 §7.5 carries the same window in the master contract.

Rail is now explicitly in scope for transportation-sector cyber risk. D09 must include a **breach notification window** (typically 72 hours), the notification channel, and what constitutes a reportable incident. Absent this, the Railroad's CISO will block the deployment regardless of what procurement agreed.

### 9. Personnel security and background checks

**Status: CLOSED** — D07 §7.7. Supplier personnel with access to Platform IP are subject to background verification; Supplier personnel require no access to Railroad systems at all, which is the structural answer. Railroad-specific screening on any on-site visit is accommodated.

Railroad IT will ask whether our engineers have background checks, and whether they will accept the Railroad's. Especially relevant given federal hazmat and security-sensitive rail requirements.

### 10. Export control and sanctions

**Status: CLOSED** — D07 §13. Mutual compliance, denied-party confirmation, no encryption beyond OS and standard libraries, no re-export without authorisation.

Even a domestic-only deployment can raise export-control questions if any component or engineer is foreign-sourced. Cheap to address in D07, expensive to discover later.

### 11. Missing: escrow

**Status: CLOSED** — D13 §4. Insolvency-triggered, running-version deposit, operability never ownership.

If AxiomDynamics ceases to exist, can the Railroad keep operating? A **source code escrow** agreement (triggered on insolvency or cessation of support) is the standard answer and is often the clause that lets a sole-source vendor be approved at all. Given that this is a company selling to organisations that plan in decades, expect this question.

### 12. Transition and exit assistance

**Status: CLOSED** — D07 §15.6. On termination for any reason except Railroad's uncured breach, 90 days at no charge: data export, transition assistance, final configuration statement. D09 §5 on retention and deletion.

What does the Railroad get on termination — data export format, a defined assistance period, and a prohibition on our retaining copies. Must be specified, not implied.

---

## Part IV — Precedence and construction

To prevent the loophole where a technical annex contradicts the master contract:

1. **D07 Comprehensive Master Contract** governs generally.
2. **D02 Master Pilot Agreement** governs during the pilot term, where it conflicts with D07.
3. **D09 Data Processing & Security Addendum** governs on data protection and security matters.
4. **D03 MSA** governs structure, ordering, and change control across all orders.
5. **D04 SOW** governs scope of work and deliverables for that specific order.
6. **A2 Rate Card** governs price. **Where any document's fee differs from A2, A2 wins.**
7. **B-series technical annexes** are descriptive and do not create warranties unless D07 expressly incorporates them.
8. **F-series forms** are administrative. Where a form conflicts with an agreement, the agreement governs. A form records an event; it does not vary a term.
9. Where a B-series document describes a capability that D07 disclaims, **the disclaimer governs and the annex must be corrected** — this is a drafting error to be fixed, not a gap to be argued.

That rule 9 is the one that keeps this docket honest over time. Rule 6 is the one that keeps the numbers honest.

---

## Part V — Build status at a glance

**Built — 36 Markdown documents plus one Excel model and one HTML one-pager (38 artifacts):** A1 ROI calculator (`.xlsx`) · **A2 rate card** · B01 blueprint · **B02 flow map** · **B03 one-page brief** · B04 tech stack · B05 data flow · C01 deployment SOP · C02 certification & assessment · **D01 preface & checklist** · D02 pilot agreement · **D03 MSA** · **D04 SOW templates** · D05 rollover mechanics · D06 support & SLA · D07 master contract · D08 licensing · D09 DPA · **D10 component register** · D11 NDA · D12 regulatory status · D13 IP & escrow · D14 operating model · **F00–F13 forms (14)** · this index.

**Not yet built — 0.** Every document identified in Part II now exists.

**All twelve identified contractual loopholes are closed.** That is a statement about the *documents*: every gap listed in Part III now has a clause that closes it. **It is not a statement that the build matches them** — four controls remain unbuilt, and they are listed in Part VI. A docket that claimed both would be claiming something the code does not support, which is the exact failure this index exists to prevent.

**The agreement layer is complete.** A customer can be taken from first conversation to executed order, through pilot, through conversion, through support, through termination, using only documents in this docket. Nothing in that chain requires an improvised document.

**Next by value:** nothing in the docket. The remaining work is not documentary — it is the four unbuilt controls in Part VI, the Phase 0 pre-signature items (LLC, EIN, insurance, bank, USPTO), and counsel review of the agreement layer. **A docket with no gaps in its index is a docket that has stopped being honest with itself; the gaps that remain are in the code and in the company formation, not in these documents.**

**Deferred by decision:** E-series assurance documents (evidence registry, air-gap media chain of custody, DR/RTO/RPO, continuous compliance, records retention, RACI) — gaps identified in library reconciliation but not needed for a BNSF pilot; candidates for Phase 2.

**Internal, moved to `assets/`:** carrier dossiers, library reconciliation, IP strategy.

**Architectural decisions locked (B01):** fully on-premise edge, zero outbound network — **both built**. Append-only disposition ledger (AD-3) — **built 2026-11-09**: insert-only write path, supersede-not-overwrite corrections, database-level `UPDATE`/`DELETE` guards, SHA-256 chain, and a signed export bundle with an independent verifier. Signed certification registry (AD-2) — **design decided, not yet built; see Part VI.** The export's *signature* exists without AD-2; its *attribution* does not, which is the distinction §4.5a of B01 exists to keep visible.

> That distinction is the whole point of this index. A locked decision is a decision. It is not a delivered control, and the two must never be written in one sentence without the difference stated.

**Commercial decision locked (D13):** AxiomDynamics retains all IP; escrow grants operability only on insolvency.

---

## Part VI — Known gaps between the docket and the build

These are disclosed rather than hidden, and they are tracked here so the docket cannot drift ahead of the code without someone noticing.

| Gap | Where disclosed | Consequence while open |
|---|---|---|
| **No detector ingest path at all** — no endpoint accepts a Railroad payload; signals are generated from physics equations on synthetic traces | B01 §7 gap #5 · **B02 §2** · **B03 status block** | **The largest gap in this table.** Every demonstration number is a demonstration of the method, not of the Railroad's data. The validation chain (schema, timestamp, plausibility) is designed and not built. |
| **The ledger export signature cannot name the signer, and replication is manual** — since 2026-11-09 the ledger exports as a signed bundle that a recipient verifies without the Platform, which detects altered/added/removed/reordered records and a ledger that has shrunk since a held bundle; but the HMAC-SHA256 signature is symmetric, cannot prove when the bundle was made, cannot detect a wipe before the first bundle in a series, and nothing ships a bundle on a schedule | B01 §4.5 · **B01 §4.5a** · B01 §7 items 11–12 · D09 §4.4 · **D09 §4.5** · **F09 Part 7** | Authentic and independently verifiable, but **not** attributable to a person or an instant, and a lost disk still loses the ledger. Do not call an export a signed certificate of authorship. |
| Certification registry is **local accounts**, no cryptographic verification | B01 §7 gap #1 · D09 §4.4 · **F08 Part 1** | Manual control via F08 is the substitute. A reviewer can self-assert a cert ID. |
| No SBOM artefact in releases | D09 §4.4 · **D09 §7.2** | Customer cannot independently verify the dependency chain. Target Q1 2027. |
| No hash pinning of dependencies | D09 §4.4 | A compromised package index could serve malware. Target Q1 2027. |
| No signed release artefacts | D09 §4.4 · **D09 §7.3** | A release archive could be substituted. Target Q2 2027. |
| Licence scope enforced **by contract only**, not by the software | D02 §6 · D05 §5.2 | Nothing technically prevents a second site. Scope is an obligation, not a control. |
| Insurance limit is **$2M, not $5M** | D07 §10.1 · D03 §9 | Stated honestly with a step-up commitment. Certificates must match the clause. |

**The rule for this table:** a gap moves from here to closed only when the code changes, and the entries in B01, D09, F08 and F09 are amended in the same commit. Documenting a fix that was not made is the exact failure this docket was built to prevent.

**Closed:** the disposition ledger append-only gap (AD-3). Closed 2026-11-09 in the commit that rebuilt `backend/store.py`, added 17 adversarial tests in `tests/test_store.py`, and amended B01 §4 and §7 item 2, D09 §4.4 and the audit-logging row, F09 Parts 6–7 and its footer, and this table. The gap did not disappear — it narrowed. What was open was "a disposition can be silently replaced"; that is now impossible. What remains is "the ledger cannot be proven untampered by a party holding the database file", and that is the row above.

**Also closed, same day:** the *unsigned* half of the row above. `backend/ledger_export.py` now writes a signed bundle and `tools/verify_ledger_export.py` verifies it without importing Platform code, so a party holding only the bundle and the key can confirm no record was altered or removed. The row was rewritten rather than deleted, because the signature introduced limits of its own — it is symmetric, it cannot date itself, and a wipe before the first bundle in a series is invisible to later ones — and a gap table that silently loses a row teaches the next reader to trust it less.

> **One correction worth recording, because this table exists to prevent it.** The first version of the export passed a total wipe: delete every row, export honestly, and a recipient holding the previous bundle was told every check passed. The checks were each individually correct and the set proved nothing, because none compared the bundle against one the recipient already had. Fixed by recording the ledger's own head in each bundle and failing when a later one reports a shorter ledger. That the gap was caught before this table claimed the control closed is the only reason the table is still worth reading.

---

*This docket index is a working structure, not a legal opinion. Every document in Part II under D must be reviewed by qualified counsel in the relevant jurisdiction before execution. Nothing here constitutes legal advice.*
