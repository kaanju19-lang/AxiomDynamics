# AxiomDynamics — Master Licensing & Liability

**Docket position:** D08. Executed under the Comprehensive Master Contract (D07). Conversion mechanics in D05. Rate schedule annexed as A2.

> **Drafting status:** Commercial grade. The pricing structure and the liability split are settled; the language is not yet contract-grade. Requires conversion to enforceable terms by counsel before execution.

**Positioning:** This is not a SaaS product. AxiomDynamics is an engineering-discipline, agentic (non-LLM) predictive maintenance platform sold against multi-million-dollar CapEx/OpEx exposure. Licensing is tied to **operational assets monitored** and **documented outcomes prevented** — not to user seats.

---

## 1. Why Not SaaS

SaaS pricing (per seat, per user, per "workflow") is the wrong instrument for this buyer and this risk profile. Railroad capital planning operates on multi-year asset economics, federal safety exposure, and derailment cost avoidance — not on per-user subscription lines.

| SaaS Model | AxiomDynamics Model |
|---|---|
| Per-seat / per-user | Per monitored axle / operational asset |
| Adoption punished (more users = more cost) | Adoption rewarded (broader coverage = more defects caught) |
| Vendor holds the data | Customer owns the deployment and the data |
| Cloud dependency | On-premise / edge, air-gap capable |
| Value claimed | Value documented against real derailment cost data |

The buyer is a Class I railroad's operating and safety organization. They do not buy seats. They buy **reduced derailment exposure** and **defensible regulatory posture**.

---

## 2. Phase 1 — External Pilot Deployment (12 months)

> **Term corrected to 12 months.** Earlier drafts said "6–12 months." **D02 §1 fixes the pilot at twelve months from the Commissioning Date**, and a business document that offers a six-month option the contract does not contain creates a promise we would be held to and did not price. If a shorter evaluation is genuinely wanted, that is a negotiated variation to D02 — not a range quoted in a proposal.

**Pilot scope**

- One major rail yard or operating division
- 100–200 active freight car axles (aggregate or unit-level)
- Edge deployment: on-premise server, no cloud dependency
- Integration with existing wayside detector hardware (HBD, wheel impact detectors)
- Human-in-the-loop reviewer workflow training
- Validation against the customer's own historical derailment and defect data

**Pilot investment breakdown**

| Component | Cost (USD) | Notes |
|---|---:|---|
| Pilot licence (12-month, one site) | $180,000 | Non-exclusive, on-premise deployment |
| Implementation support & commissioning assistance | $65,000 | **Advisory only — the Railroad performs installation** (D14 §3) |
| Training materials & certification programme | $40,000 | Curriculum, assessment instruments, registry setup |
| Validation support | $35,000 | Historical data comparison, methodology review |
| Support during pilot | $50,000 | Business-hours support per D06 §2; patches and licence administration |
| **Total Pilot Year 1** | **$370,000** | Fixed for the pilot term |

> **Corrected against A2 §5.1 and D14.** Earlier drafts of this table described the $65,000 line as "wayside hardware integration — one edge server, detector harness, networking" and the $50,000 line as "24/7 operations support." **Both were wrong and both would have created a warranty of integration and a 24/7 support obligation this company does not undertake.** The Railroad installs and supplies its own hardware; support is business-hours only with no uptime guarantee (D06 §2.4, §12.3). A2 governs price and description.

**Pilot evaluation criteria**

Per D02 §8 and D04 SOW-1 §8. **These are evaluation criteria, not performance guarantees.** Failure to meet any of them is not a breach.

| Criterion | Target |
|---|---|
| Advisories reviewed and dispositioned | 100% of advisories generated |
| Conditions surfaced not previously identified | To be observed and recorded |
| False-positive rate | To be measured; no target |
| Platform availability | To be measured; no target |
| Reviewer certification completed | 100% of designated reviewers |

> **Superseded content, recorded for integrity.** Earlier drafts of this section stated pilot "success criteria" as: detect bearing defects 18–48 hours before failure versus a ~4.8-hour legacy average; zero false-positive stop-train orders; identify 2–4 defects in six months; and a pilot-stage ROI multiple of 12x–50x. **Those were performance commitments in a commercial document that D02 §7.2 expressly disclaims.** Anyone who read them and signed D02 would hold both documents — and the contradiction would be resolved against us. The numbers may appear in A1 as modelled scenarios with stated assumptions, clearly labelled as such. They may not appear here as criteria.

---

## 3. Phase 2 — Full Deployment (Year 2+)

Once the pilot documents ROI, the railroad scales to a division or the full fleet. Licensing becomes annual and asset-based.

### Tier 1 — Core Operations License

- Up to 500 active freight car axles
- **$300,000/year** at the band rate of $600 per monitored axle
- Includes: platform licence, detector data ingest, edge deployment advisory, business-hours support per D06 §2, and monthly model and rule updates
- Billed per operational asset (axles monitored) — not per user, not per seat

> **Corrected.** Earlier drafts said this tier included "wayside integration, edge server, 24/7 support." All three were wrong: the Railroad supplies its own edge compute and performs its own integration (D14 §3), and support is business-hours with no uptime guarantee (D06 §2.4, §12.3). Corrected against A2 §6 and A2 §7.

### Tier 2 — Enterprise Operations License

- 500–2,000 axles (multiple yards or divisions)
- **$550,000/year at 1,000 axles; $1,050,000/year at 2,000 axles** — $500 per axle for the
  1,500 axles in this band
- Adds: multi-site dashboard, cross-division analytics, fleet-wide trend reporting (**not predictive scheduling — that capability does not exist and is not on the roadmap**), and the per-site platform fee structure in A2 §4

> **Corrected.** Earlier drafts said this tier included "one dedicated engineering liaison embedded with the customer." **That is prohibited by D14 §3** — no Supplier personnel are embedded in Railroad operations, and none sit under Railroad direction. What is offered instead is a named principal architect as a senior escalation contact, available remotely under D06 §6.1 Tier 3. Corrected against D14.

### Tier 3 — Full Rail Network License

- 2,000+ axles (entire network or mega-operator)
- **$2,175,000/year at 5,000 axles; $4,050,000/year at 10,000 axles** — $375 per axle above
  2,000
- Adds: network-wide anomaly correlation, multi-division reporting
- **Performance component available by election** (3% of corroborated prevented-failure cost, capped at 33% of base) — see §4 and A2 §4A. **Not included in the figures above.**
- **Not included:** regulatory reporting automation. The Platform does not file, prepare, or automate any regulatory submission, and the Customer's reporting obligations are unaffected (D12 §3, D06 §1.2). An earlier draft of this tier claimed "regulatory reporting automation"; that was a capability the Platform does not have and which the rest of this docket disclaims.

> **On the pricing structure — read this before quoting numbers.** These are marginal per-axle
> bands, not flat tier cliffs. The distinction is deliberate: a flat cliff charges more than
> double for a doubling of axles, so the customer's ROI gets *worse* as they expand — punishing
> exactly the adoption this commercial model depends on. Earlier drafts used flat tiers
> ($450K / $950K / $1.8M) and they failed on both counts: the entry tier returned only 1.5x, and
> scaling from 500 to 1,000 axles actually dropped ROI from 1.9x to 1.8x.
>
> These rates are a **pricing hypothesis validated only against modelled return, not against a real procurement conversation**. They are set so modelled return improves monotonically with fleet size — **1.77x at 500 axles rising to 3.36x at 10,000** on the basis stated in A2 §3.2 (A1's 0.05% escalation probability, $500,000 typical contained cost, three years of benefit against four years of fee). **A2 is the authoritative rate card and governs every figure in this section**; where the two differ, A2 wins. Treat the hypothesis flag as an instruction for the first real conversation, not as permission to quote a different price.

### 3.1 The second pricing axis — monitored sites

The license above prices **assets**. It says nothing about **geography**, and on a railroad those
are two different costs. Two deployments with identical axle counts are not the same job if one
is a single classification yard and the other spans eleven subdivisions. Each location needs its
own edge server, detector integration, commissioning trip, network path, and support coverage.

- **Platform fee: $45,000 per monitored location per year, beyond the first.**
- First site included in the base license.
- A "site" is one wayside detector location or one classification yard with edge compute —
  i.e. a place where the platform is physically installed and maintained.

**Why this matters more than it looks.** On a 2,200-mile corridor at the industry's 40–64 mile
detector spacing, a corridor deployment is roughly **34–55 sites** — not one. Pricing a corridor
as if it were a yard under-charges the installation work by an order of magnitude.

**The result that must not be hidden from the customer:**

| Scope | Axles | Sites | 3-yr licence cost | 3-yr site fees | 3-yr total | Cost per axle |
|---|---|---:|---:|---:|---:|---:|
| Single yard | 500 | 1 | $1,180,000 | $0 | **$1,180,000** | $2,360 |
| Same axles over a corridor | 500 | 11 | $1,180,000 | $1,350,000 | **$2,530,000** | **$5,060** |
| Thirteen divisions | 2,000 | 13 | $3,430,000 | $1,620,000 | **$5,050,000** | $2,525 |
| Full division footprint | 5,000 | 13 | $6,805,000 | $1,620,000 | **$8,425,000** | $1,685 |

> **Every cell above is computed from A2 §3 and §4, and the arithmetic is shown here so it can be checked.** Three-year licence cost = pilot $370,000 + Year 1 net ($300,000 less the $90,000 credit) + Year 2 + Year 3 at the band price. Site fees = $45,000 × (sites − 1) × 3 years. Worked: **500 axles** → $370,000 + $210,000 + $300,000 + $300,000 = $1,180,000. **2,000 axles** → $370,000 + $960,000 + $1,050,000 + $1,050,000 = $3,430,000. **5,000 axles** → $370,000 + $2,085,000 + $2,175,000 + $2,175,000 = $6,805,000. These tie to the band arithmetic in A2 §3.3 and to §5 above; **if any figure here disagrees with A2, A2 wins and this table is to be corrected.**

> **The finding, stated in a metric nobody can argue with.** Hold protection constant — the same 500 axles, the same assets, the same benefit — and spreading them across eleven sites **raises cost 114% and more than doubles unit cost**, from $2,360 per axle to $5,060 per axle. Ten additional sites each carry a $135,000 three-year charge against no additional protected asset. **That is the single most important commercial fact in this document and it must be shown, not buried: at fixed axle count, spreading across sites destroys the economics.** A corridor deployment is only defensible when the axle count rises with the site count — which is what the third and fourth rows show, and why unit cost falls there.

> **Deliberately not included: a modelled ROI column.** Earlier drafts of this table carried an "ROI" figure per row. That is removed here because the ROI depends on the customer's own derailment history and claim rate (§5, A1), and a per-row multiple computed from an assumed benefit per axle is a number we invented, not a number the customer recognises. **Cost per axle is objective; a modelled multiple is not.** Show the cost, run A1 with their inputs, and let the return be theirs.

> **A2 governs all figures.** Every number in this section is a worked illustration of the rate card's structure. Where a figure here and A2 differ, A2 wins (A2 §11, D00 Part IV rule 6).

**The corridor row is the one that matters commercially.** More than double the cost per axle to protect the same assets, because geography is charged separately and correctly. We could have hidden this by folding site fees into the licence; we show it because a customer who discovers it in invoice three stops trusting every other number we gave them.

**This is why a corridor engagement is scoped on the axle population that traverses it, not on
the cars parked along it.** At 200+ trains/day on a high-density corridor the annual axle
throughput is very large, and that is what makes corridor deployment economically sound. The
same territory with a thin traffic base is better served by a single-yard or single-division
deployment, which prices correctly and proves value first. We will recommend the smaller scope
when the numbers support it — a deployment that fails its own business case serves neither party.

---

## 4. Revenue Model — ROI-Tied Licensing

The defining departure from SaaS: a fixed base license, **plus an optional performance component** tied to documented prevented failures.

> **The performance component is an election, not a default.** It is priced in **A2 §4A** and is charged only if the Order expressly elects it. A Customer who declines pays the A2 §3 and §4 rates and nothing more. **Recommended default for a first pilot: do not offer it** — the corroboration workflow does not exist yet at a new customer, and a performance fee on an uncorroboratable event is a disputed invoice waiting to happen. Offer it at first expansion, once that workflow has been proven on real events.

**Base license (fixed):** $300K–$4.05M per year depending on axle volume, priced marginally by band, plus $45,000 per monitored site beyond the first. **A2 governs these figures.**

**Performance bonus (variable, by election):**

- When a defect flagged by AxiomDynamics is corroborated by the customer's root-cause analysis as a prevented failure, the railroad pays **3% of the prevented-failure cost avoidance** as an additional licensing fee, **capped at 33% of the annual base license**.
- The cap is essential. Uncapped, 3% of gross prevented cost runs to several times the base license and makes the structure incoherent. With the cap, the component adds **at most 33% of the base licence** — $99,000 at 500 axles, $181,500 at 1,000, $346,500 at 2,000. **Meaningful upside, strictly bounded.** An earlier draft said "$150K–$300K on a typical mid-size deployment," which is unreachable at the 1,000-axle base it describes: 33% of $550,000 is $181,500, so the top of the stated range exceeds the cap the sentence above it imposes.
- Worked example at 1,000 axles: base $550,000; corroborated prevented cost **$1,399,650** — 1.4 missed defects per 1,000 axles at A1's $999,750 expected cost, which is the same valuation §5 uses; 3% = **$41,989.50**; cap is $181,500, so the full amount is payable; total **$591,989.50**. (An earlier draft used a round $1,390,000, which produced $41,700 and a $591,700 total — **$289.50 light**, because $1,390,000 is $9,650 below the model's own output. Round numbers chosen for the example are how a document drifts from its model; the figure is now derived, not chosen. The cap arithmetic was always exact; the input was not.)
- **Operability condition (A2 §4A):** the Order must state who corroborates, what evidence is required, how a prevented failure is valued, the reconciliation cadence, and the cap. Absent all five, the component is not operable and must not be included in the Order.

**Why the structure holds**

- The railroad sees direct ROI and is motivated to expand coverage.
- AxiomDynamics captures upside from real outcomes rather than seat inflation.
- No SaaS "usage penalty" — nobody avoids the tool to control cost.
- **Documented human-review dispositions support the carrier's own diligence record** — they do not reduce federal or state reporting exposure, and the Platform does not alter any regulatory obligation (D12 §3, §5). *The earlier claim that this "reduces federal liability exposure" was wrong and has been removed; a vendor who promises regulatory relief the customer does not receive has sold them a liability.*

---

## 5. Financial Model — Three-Year Customer Journey

> **These are modelled scenarios, not forecasts, and not commitments.** Each figure depends on the customer's own derailment history, fleet composition, and detector coverage. They exist to show the shape of the economics — that the model improves with scale — not to predict an outcome. **A1 (`A1-ROI-MODEL/`) is the instrument that produces real numbers from a customer's real inputs**, and every assumption in it is exposed as an editable cell for exactly this reason.

> **Every benefit figure below is A1's output at A1's own defaults.** That is the same model, the same 0.05% escalation probability and the same $500,000 typical contained cost that §4 uses to price a prevented failure at about $993,000 — so §4 and §5 now value the same event the same way. If any input in A1 changes, these numbers change with it and this section must be recomputed. **The derivation is shown so a reader can check it rather than take it.**

**How the annual benefit is computed.** A1 sheet 2 puts detected defects at 2.1 per 500 axles per year and the incremental defect capture over legacy detection at 0.7 per 500 axles per year. Each defect caught that would otherwise have been missed is valued at A1's $999,750 expected cost (§4 above derives its worked example from exactly this figure), against the cost of the 2.1 inspections the detection triggers at $1,500 each. That is **$1,393.35 of net benefit per axle per year**: at 500 axles **$696,675**, at the 200-axle pilot **$278,670**.

**Year 1 (Pilot, 200 axles): $370,000 investment, modelled benefit $278,670**

- That is **0.75x the pilot fee. The pilot does not pay for itself, and this document will not pretend it does.** It is a twelve-month evaluation that buys a measured false-positive rate, a measured lead time on the customer's own data, and the evidence on which a conversion decision is made (D02 §8). Its value is the decision it informs, not the losses it prevents in year one.
- This is stated at 200 axles because §2 scopes the pilot at 100–200. At 100 axles the modelled benefit is $139,335 — still further from the fee.
- **The pilot does not promise even this outcome.** If the modelled return does not materialise, the correct commercial decision is not to convert.

**Year 2 (Production — Tier 1, 500 axles, 1 site): $300,000 base**

- Site fee: $0 — first site included (A2 §4)
- **Pilot licence credit applied to Year 1 only:** $210,000 net in the first production year (A2 §9)
- **Performance component: not included by default.** If elected, capped at 33% of base ($99,000). See A2 §4A and §4 above.
- **Year 1 net: $210,000 · Years 2–3: $300,000 each**

**Three-year production total after conversion: $810,000** (A2 §9). Against $370,000 of pilot fees, the four-year customer commitment is **$1,180,000**.

| Year | Fleet | Net fee | Modelled benefit | Basis |
|---|---:|---:|---:|---|
| Pilot | 200 axles | $370,000 | $278,670 | A2 §5.1; A1 at 200 axles |
| Production Y1 | 500 axles | $210,000 | $696,675 | $300,000 − $90,000 credit; A1 at 500 |
| Production Y2 | 500 axles | $300,000 | $696,675 | Locked, 0% (D05 §3.2) |
| Production Y3 | 500 axles | $300,000 | $696,675 | Locked, 0% (D05 §3.2) |
| **Four-year total** | | **$1,180,000** | **$2,368,695** | |

- Modelled four-year return: **2.01x** ($2,368,695 against $1,180,000) — a return on the *four-year commitment*, computed in A1 from the customer's own inputs once they are entered, not a per-scope figure and not a detection claim. See §3.1's note on why a per-row ROI column was removed from the corridor table: **this one is defensible because it is one model with one set of stated inputs; that one was not.**
- **The return is carried by the production years, not the pilot.** The pilot is a cost of finding out; the licence is where the value is. A customer who reads only the pilot-year figure has read the least flattering year in the table, and that is the year they should be shown first.

> **These are modelled scenarios from A1, not forecasts and not commitments.** The ROI multiple depends entirely on the customer's derailment and defect history, the value they place on a prevented event, and their claim rate. **Do not present a multiple to a customer as an expected outcome.** Present the method, the inputs, and the sensitivity — and let their own numbers produce their own figure. A modeled multiple quoted as a promise is the fastest way to convert a good faith evaluation into a dispute.

> **Reconciliation with §4.** An earlier draft of this section modelled $6M–$8M of avoided damage in the pilot year and $14M–$20M over four years, against a §4 that priced a prevented failure at about $993,000. Both cannot be right: A1's own defect arithmetic yields about $1,393 per axle per year of net benefit, so 500 axles supports roughly $700,000 a year, not $6M–$8M. §5 has been restated on A1 so that the benefit in this section and the performance fee in §4 are computed from one valuation. The earlier figures implied an annual benefit roughly nine to eleven times the model's own, and no input in A1 produces them.

**Year 3+ (Steady state — Tier 1)**

- Recurring annual licence: **$300,000** (locked through Year 3; Year 4 onward capped at 5%/yr, A2 §8)
- Performance component only if elected (A2 §4A)

---

## 6. Deal Structure — CapEx vs. OpEx

**Corrected: there is no CapEx payable to AxiomDynamics.**

The Railroad supplies, owns, and installs its own edge hardware and detector infrastructure (D14 §3, A2 §7.1). **We sell no hardware.** The $65,000 in the pilot is a *service* fee — implementation support and commissioning assistance — and is OpEx. Earlier drafts of this table listed $65,000 as "CapEx (hardware)" and a $15,000 hardware refresh in Year 3; both were wrong and both would have implied we supply equipment we do not.

| Year | CapEx to AxiomDynamics | OpEx (licence + services + support) | Total annual | Cumulative |
|---|---:|---:|---:|---:|
| 1 (pilot) | **$0** | $370,000 | $370,000 | $370,000 |
| 2 (production Y1) | **$0** | $210,000 | $210,000 | $580,000 |
| 3 (production Y2) | **$0** | $300,000 | $300,000 | $880,000 |
| 4 (production Y3) | **$0** | $300,000 | $300,000 | $1,180,000 |

**The customer's own hardware cost** — an edge server and networking at the pilot site — is theirs to procure and is not in this table. Reference specification: 4 cores, 8 GB RAM, 100 GB disk, Ubuntu 22.04 LTS or equivalent (F01 §3.4). At current commodity prices that is a low four-figure server, and stating it separately is more honest than folding it into a vendor line and calling it CapEx.

**Extending to six years**, at the locked rate through Year 3 and up to a 5% increase from Year 4 (A2 §8):

| Year | Fleet | Fee | Cumulative fee | Modelled benefit | Cumulative benefit |
|---|---:|---:|---:|---:|---:|
| 1 (pilot) | 200 | $370,000 | $370,000 | $278,670 | $278,670 |
| 2 (production Y1) | 500 | $210,000 | $580,000 | $696,675 | $975,345 |
| 3 (production Y2) | 500 | $300,000 | $880,000 | $696,675 | $1,672,020 |
| 4 (production Y3) | 500 | $300,000 | $1,180,000 | $696,675 | $2,368,695 |
| 5 (Year 4, max +5%) | 500 | $315,000 | $1,495,000 | $696,675 | $3,065,370 |
| 6 (Year 5, max +5%) | 500 | $330,750 | $1,825,750 | $696,675 | $3,762,045 |

**Six-year customer commitment: $1,825,750** at one site, against **$3,762,045 of modelled benefit — a modelled return of 2.06x.**

- **Modelled benefit is A1's figure at each year's fleet, held flat once at 500 axles.** A1 is linear in axles and years and does not escalate benefit, so neither does this table. Two effects nearly cancel over six years: the fee escalates from Year 4 under A2 §8, which drags the multiple down, while the weak 200-axle pilot year is diluted across more production years, which lifts it. The net movement is from 2.01x at four years to 2.06x at six — **close to flat, and it should be read as flat.** A vendor showing a steeper six-year curve than this would be assuming benefit growth that A1 does not model.

> **"Documented" was the wrong word and has been removed.** Nothing is documented before it happens. These are modelled projections built on published NTSB and industry cost data with the customer's own fleet inputs. **A1 produces the customer's figure from the customer's data; this document must never be used to present one.** See §5 note.

**Site count changes this table directly.** Each additional monitored location adds $45,000/year (A2 §4). A thirteen-site deployment at 2,000 axles is $1,050,000 licence + $540,000 site fees (12 × $45,000) = **$1,590,000/year**, not $1,050,000. **Confirm against A2 §3 and §4 before it leaves this office** — the site axis is where corridor deals become unprofitable, and it is the number most often left out of a proposal. **Recompute from A2 for every multi-site quote.**

---

## 7. Competitive Positioning

> **Every figure in this table is a modelled estimate or a specification target, not a measured field result.** It is a positioning document for internal and early-stage discussion. **It is not a warranty, and it must never be quoted to a customer as an achieved performance figure** — D02 §7.2 and D12 §8 disclaim detection assurance expressly, and a table like this sitting in a dossier the customer has seen is precisely how a disclaimer gets argued away.
>
> **The claims we may make, and the claims we may not:**
>
> | May say | May not say |
> |---|---|
> | "The platform computes a physics-derived risk assessment from detector data." | "The platform detects failures 18–48 hours before they occur." |
> | "The architecture is designed to surface precursor signatures earlier than threshold-based detection, subject to data availability and asset class." | "16x earlier than legacy detectors." |
> | "The false-positive rate is measured during the pilot; there is no target." (A2, D06 §4) | "<0.1% false positives." |
> | "The evaluator's own reviewers gate every advisory; no automatic stop is issued." | "Zero false-positive stop-train orders" — we do not issue stop orders at all. |

| Aspect | Legacy system | Generic ML | **AxiomDynamics (design intent, unverified)** |
|---|---|---|---|
| Detection lead time | ~4.8 hours (published legacy average) | 3–4 hours, variable | **Target: earlier precursor detection — to be measured in the pilot, no figure claimed** |
| False-positive rate | 2–5% (stops trains) | 8–12% (operator distrust) | **Measured during evaluation; no target; credit regime in D06 §4** |
| Cost model | $2M upfront + $200K/yr | Per-user SaaS ($10–50K/seat) | **$300K–$4.05M/yr licence + $45K/site (A2)** |
| Regulatory value | Limited | Limited | **Decision-support record; does not substitute for any inspection (D12 §3)** |
| Deployment time | 18–24 months | 6–12 months | **Customer-performed; typically weeks once the site is ready (C01)** |
| Vendor lock-in | 7–10 years | Perpetual (data hostage) | **3-year rolling; IP retained by supplier; full data export (D13, F13)** |

**Why the honest version is the stronger version.** A Chief Engineer who is told "we will measure it during the pilot and show you the result" will take the meeting. A Chief Engineer who is told "16x better" will ask for the field data, discover there is none, and end the meeting. The first is a scientific claim; the second is a sales claim, and Class I engineering leadership is professionally hostile to the second.

---

## 8. Pilot pitch — Class I railroad

> **Subject: Physics-based bearing defect assessment — a one-site, twelve-month evaluation**
>
> We build a physics-first predictive assessment platform for freight rail rolling stock. It ingests the detector data you already collect and produces a ranked, physically-grounded risk assessment per axle, which your certified reviewers disposition.
>
> **We are not claiming a detection rate before we have measured it on your data.** What we are offering is a **twelve-month, single-site evaluation at $370,000**, with the explicit purpose of establishing what the platform's actual behaviour is on your fleet and your detectors. The evaluation report at month twelve sets out advisories generated, conditions surfaced, false-positive volume, and the operational observations — with no performance target attached, because a target set before measurement invites an argument about the target rather than the result.
>
> **What makes the evaluation worth running:** the platform is fully on-premise, makes no outbound connections, and requires no data to leave your network. Your IT installs it themselves, from a documented procedure, with our advisory support but without our hands on your systems. If the evaluation does not justify production, you stop, keep your data, and owe nothing further.
>
> **How the commercial model works.** We license operational assets — freight car axles — not seats or users. $300,000/year covers 500 axles at one site. Beyond that, marginal bands reduce the per-axle rate as your fleet grows, and each additional monitored site is $45,000/year. A 2,000-axle deployment across thirteen divisions is $1,050,000/year in licence plus $540,000 in site fees. The full schedule is in the rate card (A2).
>
> **On conversion,** 50% of the pilot licence fee is credited against the first production year, and your rates are locked for three years (D05).
>
> **What we ask:** a signed mutual NDA, a site survey so we can confirm feasibility, and a pilot agreement. **We'll show you the method. You'll see the measurement.**

> **What this pitch deliberately no longer says, and why.** Earlier drafts opened with "we exist to prevent the East Palestine derailment from happening again," claimed 18–48 hour detection at "16x earlier," promised "2–4 major failures prevented" with "12x–50x ROI inside the pilot window," and offered a "6-month" pilot. **Every one of those was a problem:** the disaster reference is exploitative and invites a comparison we cannot substantiate; the detection figures are unmeasured; the ROI multiple is a modelled scenario, not a pilot outcome; and six months contradicts D02's twelve-month term. A pitch that overclaims is not a stronger pitch — it is a pitch that creates a document contradicting the contract the customer is about to sign.

---

## 9. Next steps

1. **A1 ROI calculator is built** (`A1-ROI-MODEL/`). Recalculate against the final A2 rate card before any customer sees it, and keep every assumption visible.
2. **Do not** compile a list of specific NTSB derailment cases "this system would have caught 18–48 hours early." **That claim cannot be substantiated before the pilot runs**, and an unsubstantiated claim in a sales deck is the fastest route to losing a Chief Engineer's confidence. What can be done honestly: present published NTSB findings on *when the failure became detectable in principle*, cite the source, and let the customer draw the inference.
3. Produce a customer-specific pricing proposal by fleet size and site count, from A2.
4. Assemble a regulatory brief that explains, accurately, what a documented human-review disposition does and does not do (D12) — **it is evidentiary support for the carrier's own diligence; it is not reduced federal liability**, and saying otherwise is a representation we cannot support.

---

*All cost and probability figures in this document are either (a) sourced from public NTSB, DOJ, and AP records, or (b) explicitly labeled modeling assumptions. See the platform's ROI module (`backend/roi.py`) for the sourced-versus-assumed breakdown before this is used in a live commercial negotiation.*
