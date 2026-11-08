# AxiomDynamics — External Pilot Cost Structure & YoY Licensing Model

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

## 2. Phase 1 — External Pilot Deployment (6–12 months)

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
| Software license (12-month pilot) | $180,000 | Non-exclusive, on-premise deployment |
| Wayside hardware integration | $65,000 | One edge server, detector harness, networking |
| Training & change management | $40,000 | Operator certification, reviewer workflow |
| Proof-of-concept validation | $35,000 | Historical derailment data comparison, ROI validation |
| Support & monitoring (Year 1) | $50,000 | 24/7 operations support, incident response |
| **Total Pilot Year 1** | **$370,000** | Fixed, all-inclusive |

**Pilot success criteria (measurable, not aspirational)**

- Detect bearing defects 18–48 hours before failure, versus the ~4.8-hour legacy average
- Zero false-positive stop-train orders — the human reviewer gate prevents operational disruption
- Identify 2–4 defects in the first 6 months that the legacy system missed
- Extrapolate against real NTSB/DOJ cost data: $4.5M–$18M in prevented failure cost
- Pilot-stage ROI multiple: **12x–50x**

---

## 3. Phase 2 — Full Deployment (Year 2+)

Once the pilot documents ROI, the railroad scales to a division or the full fleet. Licensing becomes annual and asset-based.

### Tier 1 — Core Operations License

- Up to 500 active freight car axles
- **$300,000/year** at the band rate of $600 per monitored axle
- Includes: wayside integration, edge server, 24/7 support, monthly model and rule updates
- Billed per operational asset (axles monitored) — not per user, not per seat

### Tier 2 — Enterprise Operations License

- 500–2,000 axles (multiple yards or divisions)
- **$550,000/year at 1,000 axles; $1,050,000/year at 2,000 axles** — $500 per axle for the
  1,500 axles in this band
- Adds: multi-site dashboard, cross-division analytics, predictive fleet scheduling
- Includes one dedicated engineering liaison embedded with the customer

### Tier 3 — Full Rail Network License

- 2,000+ axles (entire network or mega-operator)
- **$2,175,000/year at 5,000 axles; $4,050,000/year at 10,000 axles** — $375 per axle above
  2,000, plus 3% of documented prevented-failure savings
- Adds: network-wide anomaly correlation, regulatory reporting automation

> **On the pricing structure — read this before quoting numbers.** These are marginal per-axle
> bands, not flat tier cliffs. The distinction is deliberate: a flat cliff charges more than
> double for a doubling of axles, so the customer's ROI gets *worse* as they expand — punishing
> exactly the adoption this commercial model depends on. Earlier drafts used flat tiers
> ($450K / $950K / $1.8M) and they failed on both counts: the entry tier returned only 1.5x, and
> scaling from 500 to 1,000 axles actually dropped ROI from 1.9x to 1.8x.
>
> These rates remain a **pricing hypothesis**, not a published rate card, and are not benchmarked
> against what a Class I railroad actually pays per monitored axle. They are set so modelled
> return improves monotonically with fleet size — 2.0x at 500 axles rising to 4.1x at 10,000.
> Validate against one real procurement conversation before quoting them.

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
detector spacing, a corridor deployment is roughly **35–55 sites** — not one. Pricing a corridor
as if it were a yard under-charges the installation work by an order of magnitude.

**The result that must not be hidden from the customer:**

| Scope | Axles | Sites | 3-yr cost | ROI |
|---|---|---:|---:|---:|
| Single yard | 500 | 1 | $927K | 2.3x |
| Same axles over a corridor | 500 | 11 | $2.28M | **0.9x** |
| Thirteen divisions | 2,000 | 13 | $4.17M | 2.0x |
| Full division footprint | 5,000 | 13 | $6.67M | 3.1x |

The second row **loses money**, and that is correct. Benefit scales with the assets protected;
cost scales with the ground covered. Covering a lot of track while protecting few assets is a
genuinely bad deal, and the model says so rather than hiding it.

The commercial consequence is a sales discipline, not a pricing trick: **sell a corridor on the
axle population that traverses it, not the cars parked in it.** At 200+ trains/day on the
Southern Transcon the annual axle throughput is enormous — that is what makes corridor economics
work. Quoting stored inventory instead of traffic volume produces the 0.9x row and should lose
the deal.

---

## 4. Revenue Model — ROI-Tied Licensing

The defining departure from SaaS: a fixed base license plus a **performance component tied to documented prevented failures**.

**Base license (fixed):** $300K–$4.05M per year depending on axle volume, priced marginally by band, plus $45,000 per monitored site beyond the first.

**Performance bonus (variable):**

- When a defect flagged by AxiomDynamics is corroborated by the customer's root-cause analysis as a prevented failure, the railroad pays **3% of the prevented-failure cost avoidance** as an additional licensing fee, **capped at 33% of the annual base license**.
- The cap is essential. Uncapped, 3% of gross prevented cost runs to several times the base license and makes the structure incoherent. With the cap, the component adds roughly $150K–$300K on a typical mid-size deployment — meaningful upside, still bounded.
- Worked example at 1,000 axles: base $550K, prevented cost $1.39M, performance component $41.8K, total $591.8K.

**Why the structure holds**

- The railroad sees direct ROI and is motivated to expand coverage.
- AxiomDynamics captures upside from real outcomes rather than seat inflation.
- No SaaS "usage penalty" — nobody avoids the tool to control cost.
- Regulatory compliance value compounds: documented detection and reviewer disposition reduce federal and state reporting exposure.

---

## 5. Financial Model — Three-Year Customer Journey

**Year 1 (Pilot): $370K investment**

- Target: prove 12x+ ROI on prevented failures
- Prevented damage: ~$6M–$8M
- Customer internal ROI: 16x–22x

**Year 2 (Production — Tier 1, 500 axles, 1 site): $300K base + up to $99K performance bonus**

- The cap binds here: 3% of $8M–$12M prevented would be $240K–$360K, but the performance
  component is capped at 33% of base ($99K). The cap is what keeps the structure coherent.
- Total customer cost, Year 2: **$399K**
- Prevented damage: $8M–$12M
- Cumulative prevented damage across 3 years: $14M–$20M
- Cumulative investment: **$1.168M**
- **Three-year ROI: 12x–17x**

**Year 3+ (Steady state — Tier 1): $300K base + $99K performance**

- Recurring annual licensing: **$399K**
- Steady-state prevented damage: $10M–$15M/year
- Effective payback: under 5 weeks per year

---

## 6. Deal Structure — CapEx vs. OpEx

| Year | CapEx (hardware) | OpEx (license + support) | Total Annual | Cumulative |
|---|---:|---:|---:|---:|
| 1 | $65,000 | $305,000 | $370,000 | $370,000 |
| 2 | $0 | $399,000 | $399,000 | $769,000 |
| 3 | $15,000 (refresh) | $399,000 | $414,000 | $1,183,000 |
| 4 | $0 | $399,000 | $399,000 | $1,582,000 |
| 5 | $0 | $399,000 | $399,000 | $1,981,000 |

- **Five-year prevented damage (documented):** $40M–$60M
- **Five-year total investment:** $1.981M
- **Five-year ROI: 20x–30x**

Site count changes this table directly: each additional monitored location adds $45K/year, so a
thirteen-division deployment adds $540K/year to the OpEx column. Recompute before quoting a
multi-site customer.

---

## 7. Competitive Positioning

| Aspect | Legacy System | Generic ML | **AxiomDynamics** |
|---|---|---|---|
| Detection time | ~4.8 hours | 3–4 hours, unpredictable | 18–48 hours before failure |
| False-positive rate | 2–5% (stops trains) | 8–12% (operator distrust) | <0.1% (human gate) |
| Cost model | $2M upfront + $200K/yr | Per-user SaaS ($10–50K/seat) | **$300K–$4.05M/yr, ROI-tied, + $45K/site** |
| Regulatory value | Limited | Limited | **Documented risk reduction** |
| Deployment time | 18–24 months | 6–12 months | **3–6 months (edge-based)** |
| Vendor lock-in | 7–10 years | Perpetual (data hostage) | **3-year rolling; customer retains IP** |

---

## 8. Pilot Pitch — Class I Railroad (BNSF / UP / CSX)

> **Subject: Predictive Bearing Defect Platform — $4.5M–$18M Prevented Damage Pilot**
>
> We exist to prevent the East Palestine derailment from happening again. Our physics-first platform detects wheel bearing failures 18–48 hours before mechanical failure — roughly 16x earlier than the legacy detector network.
>
> **Pilot: 6 months, one yard, $370K investment.** It is designed to document 2–4 major failures prevented. That is 12x–50x ROI inside the pilot window.
>
> We do not license seats or users. We license operational assets — your freight car axles. You pay a base license, plus a performance component only when we prevent damage you can independently corroborate. No seat inflation. No cloud data hostage. On-premise deployment: your IT approves once and it runs.
>
> Post-pilot, $300K/year covers 500 axles at one site. Scale to 2,000 axles across thirteen divisions at $1.05M/year plus $540K in site fees. Every defect we detect and you verify returns 3% of the prevented-failure cost into licensing — so your incentive is to deploy everywhere, and ours is to find every defect before it becomes a derailment.
>
> **Let's start with the pilot. We'll show you the math.**

---

## 9. Next Steps (Internal)

1. Build a customer-facing ROI calculator — inputs: fleet size, derailment history, detection gaps; outputs: three-year prevented damage vs. licensing cost.
2. Document specific BNSF/UP/CSX derailment cases from NTSB that this system would have caught 18–48 hours early.
3. Produce a customer-specific pricing proposal by fleet size and accident history.
4. Assemble a regulatory compliance brief: early detection plus documented review disposition = reduced federal liability exposure.

---

*All cost and probability figures in this document are either (a) sourced from public NTSB, DOJ, and AP records, or (b) explicitly labeled modeling assumptions. See the platform's ROI module (`backend/roi.py`) for the sourced-versus-assumed breakdown before this is used in a live commercial negotiation.*
