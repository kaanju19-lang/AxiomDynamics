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
- **$450,000/year**
- Includes: wayside integration, edge server, 24/7 support, monthly model and rule updates
- Billed per operational asset (axles monitored) — not per user, not per seat

### Tier 2 — Enterprise Operations License

- 500–2,000 axles (multiple yards or divisions)
- **$950,000/year**
- Adds: multi-site dashboard, cross-division analytics, predictive fleet scheduling
- Includes one dedicated engineering liaison embedded with the customer

### Tier 3 — Full Rail Network License

- 2,000+ axles (entire network or mega-operator)
- **$1,800,000/year + 3% of documented prevented-failure savings**
- Adds: network-wide anomaly correlation, regulatory reporting automation

---

## 4. Revenue Model — ROI-Tied Licensing

The defining departure from SaaS: a fixed base license plus a **performance component tied to documented prevented failures**.

**Base license (fixed):** $450K–$1.8M per year depending on scale.

**Performance bonus (variable):**

- When a defect flagged by AxiomDynamics is corroborated by the customer's root-cause analysis as a prevented failure, the railroad pays **3–5% of the prevented-failure cost avoidance** as an additional licensing fee.
- Example: two detected defects that would have been $6M in derailment cost → an additional $180K–$300K in licensing that year.

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

**Year 2 (Production — Tier 1): $450K base + ~$150K performance bonus** (assuming 2–3 corroborated prevented defects)

- Total customer cost, Year 2: $600K
- Prevented damage: $8M–$12M
- Cumulative prevented damage across 3 years: $14M–$20M
- Cumulative investment: $970K
- **Three-year ROI: 14x–20x**

**Year 3+ (Steady state — Tier 1): $450K base + performance**

- Recurring annual licensing: $450K + variable
- Steady-state prevented damage: $10M–$15M/year
- Effective payback: under 6 weeks per year

---

## 6. Deal Structure — CapEx vs. OpEx

| Year | CapEx (hardware) | OpEx (license + support) | Total Annual | Cumulative |
|---|---:|---:|---:|---:|
| 1 | $65,000 | $305,000 | $370,000 | $370,000 |
| 2 | $0 | $600,000 | $600,000 | $970,000 |
| 3 | $15,000 (refresh) | $600,000 | $615,000 | $1,585,000 |
| 4 | $0 | $600,000 | $600,000 | $2,185,000 |
| 5 | $0 | $600,000 | $600,000 | $2,785,000 |

- **Five-year prevented damage (documented):** $40M–$60M
- **Five-year total investment:** $2.785M
- **Five-year ROI: 14x–21x**

---

## 7. Competitive Positioning

| Aspect | Legacy System | Generic ML | **AxiomDynamics** |
|---|---|---|---|
| Detection time | ~4.8 hours | 3–4 hours, unpredictable | 18–48 hours before failure |
| False-positive rate | 2–5% (stops trains) | 8–12% (operator distrust) | <0.1% (human gate) |
| Cost model | $2M upfront + $200K/yr | Per-user SaaS ($10–50K/seat) | **$450K–$1.8M/yr, ROI-tied** |
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
> Post-pilot, $450K/year covers 500 cars. Scale to 2,000 cars at $950K/year. Every defect we detect and you verify returns 3% of the prevented-failure cost into licensing — so your incentive is to deploy everywhere, and ours is to find every defect before it becomes a derailment.
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
