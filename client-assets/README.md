# Client Assets — AxiomDynamics

Deliverables intended to leave this building. Everything here is meant to be opened by a railroad's operating, safety, or procurement team, not by us.

Working materials that stay internal belong in `/assets`. Anything in this tree should be assumed to be forwarded to a customer.

## Structure

| Folder | Contents | Status |
|---|---|---|
| `01-executive-brief` | BNSF network operating dossier; VP/Director outcome brief | **Dossier built** |
| `02-roi-calculator` | Live Excel three-year business case, two pricing axes | **Built** |
| `03-technical-dossier` | Physics methodology, validation, architecture | Not started |
| `04-pilot-proposal` | Scoped 6-month pilot with success criteria | Not started |
| `05-commercial-terms` | Licensing structure, tier definitions, terms | Built |

## 02 — ROI Calculator

`AxiomDynamics-ROI-Calculator.xlsx` — five sheets:

1. **Your Fleet** — axle count, line speed, **site count**, and cost inputs. Yellow cells are the only places to type.
2. **Detection** — legacy vs. AxiomDynamics detection performance, and the track miles of early warning that follow from it.
3. **Benefit** — annual prevented-failure value, three-year.
4. **Licensing Cost** — two pricing axes: per-axle license (marginal bands) plus per-site platform fee. Pilot year vs. production years.
5. **Summary** — the number that matters, plus every formula above it auditable.

### Two pricing axes, because there are two cost drivers

**Axle volume drives the license.** Value scales with assets monitored, so the license does too — $600/axle for the first 500, $500 for the next 1,500, $375 above 2,000, applied marginally.

**Site count drives the platform fee** — $45,000 per monitored location beyond the first. Geography does not scale with axle count: each location needs its own edge server, detector integration, install trip, and support coverage. A single yard and a 13-division network with identical axle counts are very different deployments and cost very different amounts to serve.

### The finding the site axis exposed

| Axles | Sites | 3-yr cost | ROI | Reading |
|---|---|---|---|---|
| 500 | 1 | $927K | 2.3x | single yard — works |
| 500 | 11 | $2.28M | **0.9x** | corridor, same axles — **loses money** |
| 2,000 | 13 | $4.17M | 2.0x | 13 divisions |
| 5,000 | 13 | $6.67M | 3.1x | full BNSF division footprint |

**Benefit scales with assets protected; cost scales with geography covered.** Covering a lot of track while protecting few assets is simply a bad deal for the customer, and the model now says so instead of hiding it.

The commercial consequence: **a corridor must be sold on the axle population traversing it, not the cars parked in it.** At 200+ trains/day on the Southern Transcon the annual axle throughput is enormous — that is what justifies corridor economics. A pitch quoting stored inventory instead of traffic volume produces the 0.9x result and deserves to lose.

### A note on flat tiers (still worth recording)

Earlier drafts used flat tiers ($450K / $950K / $1.8M). They failed twice: the entry tier returned only 1.5x, and scaling from 500 to 1,000 axles *dropped* ROI from 1.9x to 1.8x, because crossing a tier boundary more than doubled the price for a doubling of axles. Marginal per-axle bands replaced them and were verified monotonic across 500 → 10,000 axles.

If you change the rate card, re-run the monotonicity check. It is the most likely thing to break.

## Verification status

Every formula recalculates clean (64 formulas, zero errors), and the summary figures were independently re-derived in Python — not just read back from the file. An error-free workbook can still be wrong; the numbers above were checked against hand calculation, and the pricing was checked for monotonic behaviour across fleet sizes.

The sensitivity that matters most: cell `B16` on sheet 1 (catastrophic escalation probability). The workbook defaults to 0.05% because 2% would imply dozens of billion-dollar derailments a year nationwide, which is physically impossible. Change it deliberately and re-read the result.
