# D03 — Master Services Agreement (MSA)

**Docket position:** D03. The umbrella. Executed once per customer; survives every individual Order. All future Statements of Work (D04) are placed under it.

**Classification:** Client-facing. Executed once, then referenced.

> **Drafting status:** Commercial grade. Requires counsel review before execution.

---

## 1. What this agreement does

This is the standing agreement between us. It is signed once. It does not describe any particular piece of work. Instead it sets the rules that apply to **every** piece of work we ever do together, so that each individual order can be short.

Think of it this way: the MSA is the rulebook; a Statement of Work is a chapter. Once the rulebook is agreed, chapters can be added without renegotiating the rules.

**This agreement governs the relationship. A Statement of Work governs the work.** Where an Order is silent, this agreement applies. Where an Order conflicts with this agreement on **scope, schedule, or price**, the Order wins for that Order only. On everything else — liability, IP, confidentiality, security, insurance — this agreement wins, and an Order cannot quietly override it.

---

## 2. Parties

**Supplier:** AxiomDynamics LLC, a Texas limited liability company, [address], [EIN if requested].

**Customer:** ______________________________ ("Railroad").

**Effective Date:** ______________________

**Term:** from the Effective Date until terminated under §12. **The Term is not fixed.** It lasts as long as there is an Order in force, plus the survival periods in §12.5.

---

## 3. Definitions

**Order** — a Statement of Work executed under this agreement, in the form of D04, or a purchase order that expressly references this agreement.

**Platform** — the AxiomDynamics software suite, as described in B01 (System Blueprint), including the documentation.

**Deliverable** — anything we are required to deliver under an Order.

**Railroad Systems** — the Customer's networks, servers, detector infrastructure, and data.

**Railroad Data** — data owned by the Customer, per D09 §2.

**Business Day** — Monday–Friday, excluding US federal holidays.

**Affiliate** — an entity controlling, controlled by, or under common control with a party.

Other capitalised terms take the meaning given in D07 or D09.

---

## 4. Structure of the relationship

### 4.1 Ordering
Work is ordered only by a signed Statement of Work. **No work is performed on verbal instruction, email approval, or handshake.** Where a Customer purchase order is required internally, it must reference this agreement and the Order number.

### 4.2 Order precedence
An Order may specify scope, schedule, personnel, deliverables, acceptance criteria, and price. An Order may **not** override this agreement or D07 on liability, indemnity, IP ownership, confidentiality, security, or insurance. Any such term in an Order is void unless both parties' authorised signatories expressly agree to it in that Order by specific written reference to the clause being varied.

### 4.3 Incorporated documents
The following form part of this agreement and are incorporated by reference:

| Document | Subject |
|---|---|
| **D07** | Comprehensive Master Contract — the full terms |
| **D09** | Data Processing & Security Addendum |
| **D06** | Technical Support, SLA & Update Governance |
| **D11** | Mutual NDA |
| **D12** | Regulatory Status & Safety-Critical Function Statement |
| **D13** | IP Ownership & Escrow Schedule |
| **D14** | Operating Model & Liability Boundary |
| **A2** | Rate Card & Band Definitions |
| **B01** | System Blueprint & Architecture |
| **B04** | Technology Stack Disclosure |
| **B05** | Data Flow & Residency Statement |
| **C01** | DIY Self-Deployment SOP |
| **C02** | Certification & Role-Based Assessment |

Where two incorporated documents conflict, the precedence order in D00 Part IV applies.

### 4.4 Conflict rule
This agreement and D07 are intended to be read together. If a genuine conflict exists between them, **D07 governs** — it is the fuller instrument and it was drafted to be the authoritative statement of the terms.

---

## 5. Our obligations

1. Perform each Order with reasonable skill and care, using personnel with the skills the work requires.
2. Deliver the Platform, documentation, and updates described in the applicable documents.
3. Meet the support response times in D06 §2.
4. Comply with D09 on data handling and security.
5. Maintain the insurance in §9.
6. Comply with applicable law.
7. Notify the Customer of a security incident per D09 §6.1.

**What we do not undertake:** we do not install the Platform (D14 §3), do not access Railroad Systems without written authorisation (D09 §3.4), do not provide operating, dispatching, inspection, or regulatory advice (D06 §1.2–1.3), and do not accept responsibility for the Customer's operating decisions (D12, D14).

---

## 6. Customer obligations

1. Perform installation, integration, configuration, and commissioning with its own personnel, and sign the Configuration Attestation (Form F02) when complete.
2. Maintain the operating environment and detector feed in working order (D07 §6).
3. Designate an authorised representative with authority to accept Deliverables and approve Changes.
4. Ensure personnel using the Platform complete certification (C02).
5. Record a disposition for every advisory generated (D02 §5, obligation 5; D06 §4.2).
6. Obtain and maintain its own regulatory compliance (D12).
7. Pay undisputed invoices per the Order and A2 §10.

---

## 7. Fees and payment

1. Fees are stated in the Order and priced from **A2 (Rate Card)**, which governs price where an Order is silent.
2. Invoicing and payment terms follow **A2 §10** unless the Order states otherwise.
3. All fees are exclusive of taxes; the Customer bears sales, use, VAT, and withholding (D02 §3.4).
4. Travel and expenses are **not included** in fixed fees and are billed at actual cost per A2 §5.3, pre-approved per Form F04, claimed per Form F07.
5. Fees are non-refundable except as expressly stated in an Order or in D06 (service credits) or D07 (termination).

---

## 8. Change control

**No change to scope, schedule, or price takes effect without a signed Change Order (Form F03).** This applies equally to changes the Customer requests and to changes we propose. A Change Order must state the change, its effect on price and schedule, and its effect on any acceptance criteria.

**Verbal or emailed agreement to a change does not bind either party.** This rule exists to protect both sides: it prevents us from doing unrequested work that later can't be invoiced, and it prevents the Customer from being surprised by a change nobody documented.

**Tolerance for minor change:** work that adds no more than **8 hours** of effort and does not affect price, schedule, or acceptance criteria may proceed on written email confirmation from both authorised representatives. Anything beyond that requires Form F03.

---

## 9. Insurance

We maintain, throughout the Term and for two years after, at our own cost:

| Policy | Limit |
|---|---|
| Commercial General Liability | $1,000,000 per occurrence / $2,000,000 aggregate |
| Technology Errors & Omissions / Professional Liability | **$2,000,000 per claim** (see note) |
| Cyber Liability | $1,000,000 per claim |
| Workers' Compensation | Statutory, where required |
| Employer's Liability | $1,000,000 |

Certificates of insurance are provided on request and on each renewal. We name the Customer as additional insured on the CGL policy where required by an Order.

> **Note on the E&O limit — read this, it is deliberately honest.** D07 §10 and §10.1 state a Technology E&O limit of **$2,000,000 per claim**, with a contractual commitment to step up to the highest commercially available limit up to $5,000,000 once revenue exceeds $1,000,000 or a production licence is executed. **$5,000,000 is not purchasable by a pre-revenue company at a premium the business can carry** — underwriters price on revenue and loss history. The commitment to step up is real and enforceable; the claim that we hold $5M today would not be, and a certificate of insurance that does not match the contract is a problem discovered at exactly the worst moment. The figures in this section and D07 §10 must always match the policies actually bound.

---

## 10. Liability

**Liability is governed by D07 §8, which applies to every Order.** In summary, and subject to D07:

1. Each party's aggregate liability is capped at the greater of twelve months' fees under the relevant Order or the amount stated in D07 §8.1.
2. Neither party is liable for indirect or consequential loss, lost profit, or lost revenue.
3. The cap does not limit liability for death or personal injury caused by negligence, fraud, breach of confidentiality, IP infringement, or anything that cannot lawfully be limited.
4. **The cap does not, and cannot, exclude a tort claim for personal injury or property damage arising from a defective product.** D07 §8.4 states this openly and this agreement adopts it.

---

## 11. Intellectual property

As set out in **D13**, which governs:

1. We retain all IP in the Platform, models, weights, rules, and documentation, including improvements.
2. The Customer owns its data, including all Railroad Data and the dispositions it records.
3. The Customer receives a non-exclusive, non-transferable licence to use the Platform for the scope and term of each Order.
4. Escrow is insolvency-triggered and grants **operability only, never ownership** (D13 §4).
5. No IP transfers to the Customer by reason of this agreement, any Order, or conversion from pilot to production.

---

## 12. Term and termination

### 12.1 Termination for convenience
Either party may terminate **this agreement** on 90 days' written notice. Termination of this agreement terminates all Orders placed under it, subject to §12.4.

### 12.2 Termination for cause
Either party may terminate on 30 days' written notice of a material breach that remains uncured.

### 12.3 Termination of a single Order
An Order may be terminated without terminating this agreement, per that Order's terms.

### 12.4 Effect
On termination: the Customer ceases use, exports its data in usable format, and pays fees accrued to the termination date. Prepaid fees for unperformed periods are refunded **only** where termination is by the Customer for our uncured breach.

### 12.5 Survival
The following survive termination: IP (§11), confidentiality (D11), liability (D07 §8), indemnity (D07 §9), data protection obligations for two years (D09 §14), and transition assistance for 90 days (D07 §15.6).

---

## 13. Independent contractor

We are an independent contractor. Nothing creates a partnership, joint venture, agency, or employment relationship. **Neither party's personnel are under the direction or control of the other** (D14 §3). No employee of ours is assigned to the Customer's operations, and none is authorised to act on the Customer's behalf.

---

## 14. Compliance and export

Both parties comply with applicable law, including export control and sanctions (D07 §13). We confirm we are not a denied party and will not re-export without authorisation. We do not incorporate encryption beyond the operating system and standard libraries (D07 §13).

---

## 15. General

**Entire agreement:** this agreement, D07, the incorporated documents, and the Orders. **Precedence:** D07 generally; this agreement on structure and ordering; an Order on its own scope and price; A2 on price.

**Amendments:** only in writing, signed by both authorised signatories. **No waiver** by delay. **Severability.** **No third-party beneficiaries.** **Assignment:** neither party without written consent, save to an Affiliate on notice or in a corporate reorganisation (D13 §6). **Notices:** to the addresses in §17, by hand, courier, or email with confirmation of receipt (Form F12 for formal notices). **Governing law and venue:** ______________________ (to be completed with counsel — Texas is the default expectation for a Texas entity contracting with a Texas-headquartered carrier).

---

## 16. Order of precedence within this agreement

1. **D07** — Comprehensive Master Contract, generally.
2. **D09** — on data protection and security matters.
3. **This agreement (D03)** — on structure, ordering, and change control.
4. **An Order (D04)** — on its own scope, schedule, and price.
5. **A2** — on price.
6. **B-series** — descriptive only; creates no warranty unless D07 expressly incorporates it.

Where a technical annex describes a capability that D07 disclaims, the disclaimer governs and the annex is corrected. That is a drafting error to fix, not a gap to argue.

---

## 17. Notices and signatures

**Supplier notices:** AxiomDynamics LLC · [address] · Attention: [name], [title] · [email]

**Customer notices:** ______________________

---

**AXIOMDYNAMICS LLC**

Name: ____________________  Title: ____________________

Signature: ____________________  Date: __________

**RAILROAD**

Name: ____________________  Title: ____________________

Signature: ____________________  Date: __________

---

*Form of agreement. Not legal advice. Requires counsel review in the governing jurisdiction before execution.*
