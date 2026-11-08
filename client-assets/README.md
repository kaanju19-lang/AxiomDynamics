# Client Assets — AxiomDynamics

Deliverables intended to leave this building. Everything here is meant to be opened by a railroad's operating, safety, or procurement team, not by us.

Working materials that stay internal belong in `/assets`. Anything in this tree should be assumed to be forwarded to a customer.

## Structure

| Folder | Contents | Status |
|---|---|---|
| `01-executive-brief` | One-page outcome brief for VP/Director level | Not started |
| `02-roi-calculator` | Live Excel three-year business case | **Built** |
| `03-technical-dossier` | Physics methodology, validation, architecture | Not started |
| `04-pilot-proposal` | Scoped 6-month pilot with success criteria | Not started |
| `05-commercial-terms` | Licensing structure, tier definitions, terms | Referenced in `/assets` |

## 02 — ROI Calculator

`AxiomDynamics-ROI-Calculator.xlsx` — five sheets:

1. **Your Fleet** — axle count, line speed, and cost inputs. Yellow cells are the only places to type.
2. **Detection** — legacy vs. AxiomDynamics detection performance, and the track miles of early warning that follow from it.
3. **Benefit** — annual prevented-failure value, three-year.
4. **Licensing Cost** — tier auto-selects from axle count; pilot year vs. production years.
5. **Summary** — the number that matters, plus every formula above it auditable.

Rebuild with `python3 build_roi_calculator.py`, then recalculate before shipping. (`build_roi_calculator.py` is kept beside the workbook on purpose — the model must be reproducible, not a mystery binary.)

### What the model actually says

Pricing is **marginal per-axle**, not flat tiers. Each band charges only for the axles inside it, so adding axles never costs more than the value those axles create. At the defaults:

| Axles | Primary band | Base license | Annual benefit | 3-yr cost | 3-yr net | ROI | Pilot payback |
|---|---|---|---|---|---|---|---|
| 500 | Band 1 — Core | $300K | $697K | $1.05M | $1.04M | 2.0x | 5.8 months |
| 1,000 | Band 2 — Enterprise | $550K | $1.39M | $1.65M | $2.53M | 2.5x | 2.9 months |
| 2,000 | Band 2 — Enterprise | $1.05M | $2.79M | $2.85M | $5.51M | 2.9x | 1.4 months |
| 5,000 | Band 3 — Network | $2.18M | $6.97M | $5.63M | $15.3M | 3.7x | 0.6 months |
| 10,000 | Band 3 — Network | $4.05M | $13.9M | $10.2M | $31.6M | 4.1x | 0.3 months |

Rate card: $600/axle for the first 500, $500 for the next 1,500, $375 above 2,000 — editable in one block on the Licensing Cost sheet.

### Two pricing faults found and fixed

Worth recording, because both were invisible in a clean recalc and both would have been damaging in a customer meeting.

**1. The deal did not clear at Tier 1.** At the original $450K flat price, a 500-axle deployment returned 1.5x over three years. That will not pass a Class I procurement committee. Fixed by lowering the entry price rather than inflating the benefit side — the prevented-damage figures rest on sourced cost data and should not be bent to rescue a ratio.

**2. Flat tier cliffs punished expansion.** After the first price cut, 1,000 axles returned *less* than 500 (1.8x vs 1.9x), because crossing from Tier 1 to Tier 2 more than doubled the price for a doubling of axles. A customer expanding their fleet would see their ROI fall — the opposite of the incentive the commercial model depends on. Fixed by switching to marginal per-axle bands, which was verified monotonic across 500 → 10,000 axles.

If you change the rate card, re-run the monotonicity check. It is the single most likely thing to break.

## Verification status

Every formula recalculates clean (64 formulas, zero errors), and the summary figures were independently re-derived in Python — not just read back from the file. An error-free workbook can still be wrong; the numbers above were checked against hand calculation, and the pricing was checked for monotonic behaviour across fleet sizes.

The sensitivity that matters most: cell `B16` on sheet 1 (catastrophic escalation probability). The workbook defaults to 0.05% because 2% would imply dozens of billion-dollar derailments a year nationwide, which is physically impossible. Change it deliberately and re-read the result.
