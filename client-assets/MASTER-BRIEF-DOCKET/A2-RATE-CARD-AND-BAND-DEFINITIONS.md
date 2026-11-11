# A2 — Rate Card & Band Definitions

**Docket position:** A2. The authoritative price schedule for every commercial document in this docket.

**Classification:** Client-facing. May be shown to the Railroad.

> **Drafting status:** Commercial grade. **This document supersedes every fee figure in D02, D05, and D08.** Where a fee in any other document differs from this schedule, this schedule governs for price (D00 Part IV, rule 4).
>
> **Effective date:** ______________________  **Version:** 1.0
> **Rate lock:** fees in this schedule are held for the duration stated in §8.

---

## 1. What this document is, and why it exists

Every contract in this docket needs to cite **one** place for price. Without that, the pilot agreement quotes one number, the rollover agreement quotes a second, and the licence document quotes a third. The first time a customer's procurement analyst puts all three side by side, the discrepancy becomes a negotiating lever against you.

This schedule is that one place. It states:

1. **What we charge for** — the units of measure.
2. **How much** — the bands and rates.
3. **What is included** at each level.
4. **What is not included** and therefore separately priced.
5. **When invoices are issued** and when they are due.

**Two pricing axes, and they measure different things.** The licence axis prices **assets** — how many freight car axles we monitor. The platform axis prices **geography** — how many physical places we install equipment at. These are genuinely different costs and collapsing them into one number is the mistake that makes corridor deployments unprofitable. See §4.

---

## 2. Definitions used in this schedule

**Monitored Axle.** One freight car axle from which the platform receives, processes, and produces advisories. An axle is counted once, regardless of how many times it passes a detector. Locomotive axles are not counted unless expressly agreed in an Order.

**Site.** One physical location where the platform is installed and maintained — one wayside detector location, or one classification yard with edge compute. A site requires its own edge server, detector integration, network path, commissioning, and support coverage.

**First Site.** The single site included in the base licence. Every additional site attracts the platform fee in §4.

**Pilot.** The fixed-term, single-site, evaluation engagement under D02.

**Production Licence.** An annual licence under D08, following conversion from a pilot under D05, or purchased directly.

**Order.** A Statement of Work under D04, executed under the MSA (D03).

**Band.** A marginal price tier. Axles are priced band by band, cumulatively — **not** at a single flat rate for the whole count. §3.2 explains why, and it matters to the customer.

**Commissioning Date.** The date the Railroad signs the Configuration Attestation (Form F02) confirming the platform is operational at a site.

**Business Day.** Monday to Friday, excluding US federal holidays.

---

## 3. Axis one — Per-axle licence

### 3.1 The bands

| Band | Axles in this band | Rate per axle per year | Cumulative annual licence at top of band |
|---|---|---:|---:|
| **Band 1** | First 500 axles | **$600** | $300,000 |
| **Band 2** | Next 1,500 axles (501–2,000) | **$500** | $1,050,000 |
| **Band 3** | Above 2,000 axles | **$375** | $2,175,000 at 5,000 · $4,050,000 at 10,000 |

### 3.2 Why the bands are marginal, not flat tiers

A flat tier structure charges a single rate for the whole axle count. That produces a cliff: a customer with 501 axles pays the 500–2,000 rate on **all 501**, so doubling their fleet more than doubles their bill, and their return on the platform gets **worse** as they expand.

That is the opposite of what a fleet-scale economics product should do. Marginal bands mean the rate falls as volume rises, the customer's modelled return improves monotonically with fleet size — **1.77x at 500 axles, rising to 3.36x at 10,000** — and expansion is rewarded rather than punished.

**The basis of those figures is stated here rather than left to inference:** net three-year benefit computed from the A1 model at its own defaults — a **0.05%** probability that a missed defect escalates to a catastrophic event, a **$500,000 typical** contained derailment cost, and the sourced $1,000,000,000 catastrophic cost — measured against the four-year fee commitment at list price **net of the §9 conversion credit** ($1,180,000 at 500 axles, which is the §9 four-year total exactly). **The pilot year is charged in full and credited with no benefit at all**, which is the reason this figure is lower than the one in D08 §5: that section credits the pilot year with the modest benefit a 200-axle pilot actually produces, so it lands slightly higher (2.01x at 500 axles) on the same inputs. Neither number is wrong; they answer different questions. **On a basis that also disallows the conversion credit the figures are 1.65x and 3.34x** — quote whichever basis the conversation actually assumes, and never mix the two in one table. Recompute from A1 if any of those three inputs changes.

The customer will understand this the moment it is explained, and it is worth explaining, because a procurement analyst who spots what looks like a cliff will assume it is a negotiating tactic. It is not; it is a band structure, and the arithmetic in §3.3 shows it.

### 3.3 Worked calculation — the arithmetic a procurement analyst will do

**Example A — 500 axles, one site**

| | Axles | Rate | Amount |
|---|---:|---:|---:|
| Band 1 | 500 | $600 | $300,000 |
| Band 2 | 0 | — | $0 |
| Band 3 | 0 | — | $0 |
| **Licence subtotal** | | | **$300,000** |
| Site fee (first site included) | | | $0 |
| **Annual total** | | | **$300,000** |

**Example B — 1,000 axles, three sites**

| | Axles | Rate | Amount |
|---|---:|---:|---:|
| Band 1 | 500 | $600 | $300,000 |
| Band 2 | 500 | $500 | $250,000 |
| Band 3 | 0 | — | $0 |
| **Licence subtotal** | | | **$550,000** |
| Site fee (2 additional × $45,000) | | | $90,000 |
| **Annual total** | | | **$640,000** |

**Example C — 5,000 axles, 20 sites (a corridor deployment)**

| | Axles | Rate | Amount |
|---|---:|---:|---:|
| Band 1 | 500 | $600 | $300,000 |
| Band 2 | 1,500 | $500 | $750,000 |
| Band 3 | 3,000 | $375 | $1,125,000 |
| **Licence subtotal** | | | **$2,175,000** |
| Site fee (19 additional × $45,000) | | | $855,000 |
| **Annual total** | | | **$3,030,000** |

Example C is the number that must be shown to a customer considering a corridor deployment, and it is the number most vendors hide. At 40-mile detector spacing, a 2,200-mile corridor is roughly 34–55 sites. The site axis is not a rounding error on a corridor; at 55 sites it is $2,430,000 against a licence of $2,175,000. Roughly half the annual cost of a corridor deployment is geography, not assets. Stating that plainly is what makes the proposal credible.

### 3.4 Axle count changes during a term

**Increase.** The Railroad notifies us of the new count. The additional axles are priced at the applicable band rate, pro-rated from the first day of the following month to the end of the then-current term. No penalty, no renegotiation.

**Decrease.** Fees are not reduced retroactively. The new count applies from the next renewal anniversary.

**Reason:** the licence is a capacity commitment, not a usage meter. We provision and support for the committed count. A customer who wants true usage-based billing is asking for a different product, and it would price higher per axle because the volume risk moves to us.

---

## 4. Axis two — Per-site platform fee

| Item | Amount |
|---|---:|
| First site | **Included in the base licence** |
| Each additional site | **$45,000 per site per year** |

**What the site fee covers:** the edge server installation and configuration advisory, detector integration at that location, commissioning support, network path verification, per-site monitoring in the support queue, and the per-site quarterly performance report.

**Why it is separate from the axle fee.** Two deployments with identical axle counts are not the same job if one is a single classification yard and the other spans eleven subdivisions. Each location needs its own edge compute, its own integration, its own commissioning trip, and its own support coverage. Pricing geography as if it were a yard under-charges the work by an order of magnitude — and the shortfall only becomes visible after the deployment invoices arrive.

**What the site fee does not cover:** travel to the site (see §5.3), installation labour (the Railroad performs installation under D14), or on-site support beyond the included commissioning assistance.

---

## 4A. Axis three — the performance component (optional, offered only by election)

**This is not part of the base price and is not charged unless the Customer elects it in writing in the Order.**

D08 §4 describes a performance component: **3% of the cost of a prevented failure that the Customer's own root-cause analysis corroborates**, capped at **33% of the annual base licence**.

**Why it is an election and not a default:**

1. **It requires a corroboration process the Customer must operate.** Someone in the Customer's organisation has to attribute a prevented failure. That is real work, and it cannot be imposed.
2. **It is unenforceable without that process.** A performance fee on an uncorroboratable event is a disputed invoice waiting to happen.
3. **It is inappropriate during a pilot**, where the whole purpose is to discover whether the platform's assessments are worth acting on (D02 §8).

**If elected, the Order must state:** who corroborates, what evidence is required, the valuation method for a prevented failure, the reconciliation cadence, and the cap. Absent all five, the component is not operable and must not be included.

**Base pricing never depends on it.** A customer who declines the performance component pays the §3 and §4 rates and nothing more. A customer who elects it accepts additional upside **and** additional audit obligation. **Recommended default: do not offer it on a first pilot.** Offer it at first expansion, once the corroboration workflow has been proven on real events.

### 5.1 Pilot fees (D02)

| Component | Amount | Includes | Does not include |
|---|---:|---|---|
| **Pilot licence** (12 months, one site) | **$180,000** | Platform licence for one site, documentation, update packages during the term | Additional sites; production use |
| **Implementation support & commissioning assistance** | **$65,000** | Remote advisory support during the Railroad's installation; readiness review; commissioning checklist walkthrough | Installation labour; on-site attendance (see §5.3) |
| **Training materials & certification programme** | **$40,000** | Curriculum, assessment instruments, **manual certification register maintained per C02 §5**, up to 25 candidate assessments | Delivery of training itself; re-assessment of unsuccessful candidates (see §6); **binding of registry keys to authenticated accounts — not built (D09 §4.4, target Q2 2027)**. The registry and per-reviewer keys themselves were built 2026-11-11 |
| **Validation support** | **$35,000** | Historical data comparison, methodology review, written validation findings | Independent third-party validation |
| **Support during pilot** | **$50,000** | Defect correction, patches, licence and certification administration, per D06 §2 | Premium/out-of-hours support; custom development |
| **Total pilot fee** | **$370,000** | | |

**Payment schedule:** 40% ($148,000) on signature · 30% ($111,000) on Commissioning Date · 30% ($111,000) on completion of month six. Net thirty days. See Form F05 (Payment Terms Schedule).

**Conversion credit.** On conversion to a production licence under D05 within 90 days of pilot expiry, **50% of the pilot licence fee ($90,000)** is credited against the first production term. No other component is creditable. See §9 for the arithmetic.

### 5.2 Discovery and prototype fees (D04 SOW-3 and SOW-4)

| Service | Amount | Notes |
|---|---:|---|
| **Feasibility & Physics Assessment** (discovery) | **$45,000 – $75,000** | Fixed fee, quoted per engagement based on asset class and data availability. 50% at Order signature, 50% on report delivery. |
| **Prototype development** | **$150,000 – $400,000** | Milestone-billed: 30% kickoff, 40% demonstration, 30% acceptance. Quoted per Order. |

Ranges are quoted rather than fixed because scope genuinely varies by failure mode and data quality. A fixed schedule with ranges is honest; a single number would be invented.

### 5.3 Travel and expenses

**On-site attendance is optional and is not included in any fixed fee.**

| Item | Basis |
|---|---|
| Airfare | Economy class, actual cost, no markup |
| Lodging | Standard business class hotel, actual cost, no markup |
| Meals and incidentals | Per diem at the applicable US GSA rate for the destination |
| Ground transport | Actual cost (rental, rideshare, parking) |
| **Pre-approval** | Required in writing before booking (Form F04) |
| **Cap per trip** | **$6,000** unless a higher cap is pre-approved in writing |
| **Receipts** | Required for all items; submitted within 14 days of return (Form F07) |

**Business development travel is never billable.** Flights to a corridor for a pre-contract conversation, a relationship meeting, or a capability briefing are our cost. Travel is billable only when it occurs because a customer asked us to attend their deployment under an executed Order.

**Book through the Railroad's travel system where required.** Many Class I carriers mandate this for vendor travel. Comply. It costs nothing and removes an audit objection.

### 5.4 Training and certification fees

| Item | Amount |
|---|---:|
| Curriculum and assessment package (one-time, per customer) | Included in pilot §5.1 |
| Additional candidate assessment beyond the 25 included | **$450 per candidate** |
| Re-assessment after a failed attempt | **$450 per candidate** |
| Recertification (on the three-year cycle, C02 §4.1) | **$200 per Reviewer** |
| On-site certification workshop (per day, plus travel under §5.3) | **$3,500 per day** |

### 5.5 Professional services (rate card)

| Role | Day rate |
|---|---:|
| Principal Systems Architect | **$2,400** |
| Senior Engineer | **$1,800** |
| Engineer | **$1,350** |
| Technical writer / training specialist | **$950** |
| Support engineer (extended or out-of-hours) | **$1,100** |

A day is eight hours. Travel days are billed at 50% of the applicable day rate where work is performed en route; travel days with no work are not billed.

**Professional services are always ordered by a written SOW (D04).** No professional services are performed on verbal instruction. This rule is not bureaucracy — it is what prevents the "small favour" from becoming an unbilled month.

---

## 6. What is included at no additional charge

Included in every active licence, pilot or production:

1. Software licence for the committed axle count and site count.
2. Documentation set (B01, B04, B05, C01, C02) in current version.
3. Defect correction and security patches, per D06 §3.
4. Support at the response times in D06 §2, during business hours.
5. Licence and certification registry administration.
6. Quarterly performance report (production licences only, D06 §5.1).
7. Data export in usable format at any time, and at termination (D07 §15.6).
8. Escrow deposit of the running version, per D13 §4.

**Nothing in this list is optional, and none of it is separately chargeable.** A customer who has to buy "support" as an add-on has been sold a licence they cannot operate.

---

## 7. What is not included

1. **Installation labour.** The Railroad installs. We advise (D14 §3). This is a liability boundary, not a cost saving.
2. **On-site attendance** beyond included commissioning assistance — priced per §5.3.
3. **Custom model development** or customer-specific physics models — priced per §5.5 under an Order.
4. **Major version upgrades** — priced per Order (D06 §3.5).
5. **Regulatory or audit support** — out of scope (D06 §1.2).
6. **Operating, dispatching, or inspection advice** — not merely out of scope; **prohibited** (D06 §1.4 as amended).
7. **Third-party software licences** required in the Railroad's environment.
8. **Taxes** — all fees are exclusive of sales, use, VAT, withholding, and similar (D02 §3.4).

---

## 8. Fee protection and increases

| Period | Protection |
|---|---|
| Pilot term | Fees fixed for the pilot term (D02 §3) |
| Production Years 1–3 | **0% increase** — locked at the converted rate (D05 §3.2) |
| Production Year 4 onward | Increase capped at **5% per year**, on 90 days' written notice |
| New sites added mid-term | Priced at the rate card in force at the date of the Order; locked for that site's initial term |
| Professional services day rates | Held for 12 months from the Effective Date; thereafter reviewed annually, cap 5% |

**Rates are held for the customer, not for us.** Once a customer has a signed Order, the rate in that Order does not move for its term regardless of what happens to this schedule. A rate card is a published offer, not a floating price.

---

## 9. Rollover arithmetic — worked example

A customer completes a 12-month pilot at one site, then converts within 90 days and scales to **500 axles** in production. **The pilot itself runs at the 100–200 axles D02 and D08 §2 scope it at** — the 500-axle figure below is the production fleet it converts to, and the pilot fee is axle-independent, so the conversion arithmetic is the same either way.

| Line | Amount |
|---|---:|
| Pilot fees already paid | $370,000 |
| — of which pilot licence | ($180,000) |
| **Year 1 production licence** (500 axles × $600) | **$300,000** |
| Site fee (first site) | $0 |
| **Gross Year 1 production fee** | **$300,000** |
| Less: pilot licence credit (50% × $180,000) | **–$90,000** |
| **Net Year 1 production fee** | **$210,000** |
| **Year 2** (locked, 0%) | $300,000 |
| **Year 3** (locked, 0%) | $300,000 |
| **Three-year net total after conversion** | **$810,000** |

**The number to show the CFO:** the customer's three-year net production cost is $810,000, against $370,000 already spent on the pilot — a total of $1,180,000 across four years for one site at 500 axles. If the modelled avoided-loss figure does not comfortably exceed that, the deal should not close, and saying so early is better than discovering it at the CFO's desk.

---

## 10. Invoicing and payment

1. **Currency:** USD.
2. **Terms:** net thirty days from invoice date.
3. **Method:** ACH or wire per the remittance details on the invoice. Never by card.
4. **Disputes:** a disputed line must be notified in writing within 15 days; undisputed lines remain payable.
5. **Late payment:** 1.0% per month on undisputed overdue amounts, or the maximum permitted by law if lower.
6. **Withholding:** the Railroad bears any required withholding and provides documentation sufficient for us to claim credit.
7. **Purchase orders:** where a PO number is required, it must be issued before the invoice, not after. An invoice without a valid PO is the most common cause of a 60-day payment delay.

---

## 11. Order of precedence

Where this schedule conflicts with any other document in the docket on a matter of **price**, this schedule governs. Where an executed Order states a price, the Order governs for that Order's scope and term. On every other matter, D07 governs generally and D02 governs during the pilot — see D00 Part IV.

---

## 12. Validity and change

This schedule takes effect on the Effective Date and remains in force until superseded. It may be revised on 90 days' written notice to customers with active Orders; **revisions never apply to an Order already in force.**

---

*This rate card is a commercial document, not legal advice. Executed Orders and counsel-reviewed contracts govern the relationship. All figures are in US dollars.*
