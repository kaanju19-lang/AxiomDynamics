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

At the defaults, across three fleet sizes:

| Axles | Tier | Annual benefit | 3-yr cost | 3-yr net value | ROI | Pilot payback |
|---|---|---|---|---|---|---|
| 500 | Tier 1 — Core | $697K | $1.38M | $705K | 1.5x | 5.8 months |
| 2,000 | Tier 2 — Enterprise | $2.79M | $2.63M | $5.73M | 3.2x | 1.4 months |
| 5,000 | Tier 3 — Network | $6.97M | $4.79M | $16.1M | 4.4x | 0.6 months |

**The finding worth acting on: the economics barely clear at 500 axles.** A 1.5x three-year ROI will not move a Class I procurement committee — it reads as marginal, and the honest reaction to a 1.5x pitch is "come back when it's 3x." The deal works at 2,000 and looks strong at 5,000.

That points at one of two changes before this is shown to a customer, and it is a commercial decision, not a modeling one:

- **Lower the Tier 1 base license** from $450K toward ~$325K, which lifts 500-axle ROI to roughly 2.2x while keeping the tier credible, or
- **Raise the Tier 1 floor** to ~1,000 axles, so the entry price buys an asset base that justifies it.

Do not fix this by inflating the benefit side. The prevented-damage figure is already driven by sourced cost data; the lever that is genuinely wrong is the price, not the physics.

## Verification status

Every formula recalculates clean (61 formulas, zero errors), and the summary figures were independently re-derived in Python — not just read back from the file. An error-free workbook can still be wrong; the numbers above were checked against hand calculation.

The sensitivity that matters most: cell `B16` on sheet 1 (catastrophic escalation probability). The workbook defaults to 0.05% because 2% would imply dozens of billion-dollar derailments a year nationwide, which is physically impossible. Change it deliberately and re-read the result.
