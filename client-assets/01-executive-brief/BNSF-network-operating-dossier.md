# BNSF Railway — Network Operating Dossier

**Purpose:** know their operating structure well enough to speak in their units, their geography, and their scale — before the first meeting. Every figure below is cited; anything unsourced is labelled as such.

**Status:** BNSF only. UNP, CN, NS and CPKC follow the same template. See "Replicating this for other Class I carriers" at the end.

---

## 1. Scale — the numbers to know cold

| Metric | Figure | Source |
|---|---|---|
| Route miles | ~32,500 | [BNSF fact sheet](https://www.bnsf.com/bnsf-resources/pdf/about-bnsf/fact_sheet.pdf) |
| States served | 28, plus 3 Canadian provinces | BNSF fact sheet |
| Operating divisions | 13, grouped into 3 regions (North, Central, South) | BNSF fact sheet / [Wikipedia](https://en.m.wikipedia.org/wiki/Burlington_Northern_and_Santa_Fe) |
| Employees | ~36,500 | BNSF fact sheet |
| Locomotives | ~6,800 | BNSF fact sheet |
| Average trains per day | ~1,300 | BNSF fact sheet |
| Carloads shipped (2024) | 9.6 million | BNSF fact sheet |
| Intermodal shipments (2024) | 5.26 million units | BNSF fact sheet |
| Automotive (2024) | 3.1 million vehicles | BNSF fact sheet |
| Bridges / tunnels | 13,000 bridges, 89 tunnels | BNSF fact sheet |
| Ports served | 40+ | BNSF fact sheet |
| Intermodal facilities | 26 | BNSF fact sheet |
| Parent | Berkshire Hathaway | — |

**Structural detail worth using:** the system is organised into **13 operating divisions across three regions** — North, Central, and South. Each division is composed of subdivisions: usually one main line plus branches. Division headquarters are at California (San Bernardino), Chicago, Gulf/Red River (Spring, TX), Kansas (Kansas City), Los Angeles, Montana (Billings), Nebraska/Heartland (Lincoln), and Northwest (Seattle). A 14th division, Colorado, was folded into the Powder River Division.

This matters commercially: **"division" is the natural unit of enterprise expansion, and "subdivision" is the natural unit of site count.** When BNSF describes deploying across a region, they mean three divisions. When they describe a corridor, they mean the subdivisions it spans.

## 2. The two corridors

**Southern Transcon** — BNSF's busiest asset and their main intermodal artery.

- **~2,200 miles**, Los Angeles / San Bernardino to Chicago
- Carries roughly **70% of BNSF intermodal volume** and about a **third of all North American intermodal traffic**
- **11 subdivisions across nine states**: California, Arizona, New Mexico, Texas, Oklahoma, Kansas, Missouri, Iowa, Illinois
- Traffic density: historically ~90 trains/day on Belen–Clovis NM, now cited at **200+ trains daily**, with ~300 trains in motion systemwide at any moment
- **Nearly all double-tracked** as of the Nov 2024 Emporia Sub cutover — only ~1.5 miles of single track remains at Sibley MO and ~3 miles at Alva OK. Cajon Pass is triple/quadruple track
- Speed context: UPS "Z" trains run LA–Chicago in ~49 hours; Q trains average ~71 hours Barstow–Chicago

**Northern Transcon** — Seattle to Chicago, assembled from the Great Northern, Northern Pacific, and SP&S lines.

**Why the Southern Transcon is the right place to start a pilot:** it is their highest-density, highest-consequence corridor, it is almost entirely double-track (so a set-out has somewhere to go), and it runs through nine states — which means nine state-level regulatory environments and one very visible private-sector customer.

## 3. The detector network — the actual "site" unit

This is the single most important structural fact for our pricing model.

- **Hot bearing detectors (HBDs)**: roughly 6,000+ units across North America, typically spaced **40–64 miles apart**
- Historical FRA analysis settled on **30-mile spacing** as optimal for high-density main line (~5,800 detectors for 204,000 route miles)
- A 2017 spacing study found the detection-rate curve plateaus around **15 miles**; 7.5 vs 15 miles showed no statistically significant difference, while 15 vs 20 miles did
- **HBD installation and inspection is not FRA-regulated.** AAR Circular OT-55-R carries recommended practices. NTSB has recommended FRA establish requirements (R-24-02 through R-24-05)
- **Acoustic bearing detectors (ABD)** detect rolling-surface defects before overheating, and because of the longer warning window **far fewer units are needed** than HBDs

**The pricing implication is direct.** On a 2,200-mile corridor at 40–64 mile detector spacing, the detector population is roughly **34–55 locations** — $1.49M–$2.43M/year in platform fees at $45K/site. That is the real site count for a corridor deployment — not "one corridor, one site." Our calculator's platform-fee axis exists precisely because a corridor and a yard are not the same deployment.

## 4. What the model says at BNSF scale

Running the ROI calculator across realistic BNSF-shaped deployments:

| Axles | Sites | Base license | Site fee | 3-yr cost | ROI | Payback |
|---|---|---|---|---|---|---|
| 500 | 1 | $300K | $0 | $927K | 2.3x | 4.9 mo |
| 500 | 11 | $300K | $450K | $2.28M | **0.9x** | 12.7 mo |
| 2,000 | 1 | $1.05M | $0 | $2.55M | 3.3x | 1.2 mo |
| 2,000 | 13 | $1.05M | $540K | $4.17M | 2.0x | 3.6 mo |
| 5,000 | 13 | $2.18M | $540K | $6.67M | 3.1x | 1.4 mo |
| 50,000 | 13 | $19.1M | $540K | $44.2M | 4.7x | 0.1 mo |

**The finding that matters — and it is a genuine economic truth, not a modeling artifact:**

Row 2 loses money. 500 axles spread across 11 subdivisions returns **0.9x**. The reason is structural: benefit scales with *assets protected*, while cost scales with *geography covered*. Covering a lot of track while protecting few assets is a bad deal for the customer, and we should not pretend otherwise.

Which means a corridor must be sold on the axle population **traversing** it, not on the cars parked in it. At 200+ trains/day over the Southern Transcon, the axle population passing a detector per year is enormous — that is the number that justifies corridor economics. Any pitch that quotes a corridor's stored inventory instead of its traffic volume will produce the 0.9x result and deserves to lose.

## 5. Regulatory and political context

- East Palestine (Feb 2023) was Norfolk Southern, not BNSF — but **BNSF had an acoustic bearing detector that returned a "noisy" fault code** on the suspect car, per NTSB's investigation. That is a directly relevant, citable fact: their acoustic detection layer already existed and already flagged something. Our pitch is not "buy a new sensor," it is "fuse the signals you already have, and put a reviewer in front of them."
- NTSB recommended FRA regulate HBD installation and inspection (R-24-02 to R-24-05). Currently unregulated — a window in which a carrier can adopt voluntarily and be the example rather than the target of a rule.
- NS moved a train 13 miles to a siding after a 170°F-over-ambient alarm and it derailed en route. Response discipline matters as much as detection. Our human-in-the-loop disposition record is a direct answer to that finding.

## 6. What we do not know (and must not pretend to)

Stated plainly, because walking into a BNSF meeting with a gap papered over is worse than naming it:

- **BNSF's own detector spacing** is not public. The 40–64 mile figure is an industry norm, not a BNSF specification.
- **BNSF's freight car fleet count** was not in the sources retrieved. Carloads and intermodal units are published; fleet size is not.
- **BNSF's actual derailment cost per event** is not published in a comparable form.
- **BNSF's current detector hardware vendor mix** is unknown to us.

Each of these is a question to ask in the room, not a number to assert. Asking a well-framed question about their detector spacing demonstrates study; stating a wrong figure because it was the industry average destroys credibility permanently.

---

## 7. Replicating this for other Class I carriers

Same template, in this order: (1) route miles, divisions, states; (2) the two or three named corridors that carry the volume; (3) traffic density and running hours on those corridors; (4) detector footprint; (5) the specific derailment history that makes bearing failure salient to *that* carrier.

> **Correction to the original plan.** This section previously listed UNP, CN, CP and NS as four independent prospects. **UNP and NS are one company pending STB approval** — Union Pacific is acquiring Norfolk Southern for $85B, accepted as complete by the STB on 28 May 2026, expected to close H2 2027. See `UP-NS-combined-network-dossier.md`. Pitching them separately would be the single most damaging mistake available to us in this market.

**Build order, revised:**

**BNSF — first, and the frame has changed.** BNSF petitioned the STB to dismiss the UP–NS merger. They are now the opposing litigant in the largest rail consolidation in a generation, which means they are under pressure to demonstrate they run the safer network. The pitch is not "save money" — it is "be the railroad that proved bearing failures get caught 18 hours out, while the merger argument is on the front page." Time-limited to the STB proceeding.

**UP / NS — one combined dossier, already written.** $85B merger; the Sunset Route is structurally the Southern Transcon's analogue but carries ~28–39 trains/day against BNSF's 200+, so **corridor economics do not transfer at the same price point**. Lead with a single-division deployment instead of a corridor. Large commitments are not buyable pre-close due to capex restrictions; a $370K pilot is.

**CN / CPKC — third.** Canadian regulatory frame. The value proposition shifts from FRA exposure toward Transport Canada compliance and cross-border hazmat routing. Note CPKC's distinctive risk profile: the only single-line railroad connecting Canada, the US and Mexico.

**CSX — fourth.** Eastern network, heavy hazmat corridor exposure through the Appalachians and Northeast. Also moved to dismiss the UP–NS merger.

For each, the calculator needs only two changed inputs: axles in scope and site count. The physics does not change. **The traffic density does, and that is what decides whether corridor pricing works.**

---

*Sourcing note: BNSF figures are from the BNSF fact sheet and public industry sources; detector spacing is industry-wide (AAR/FRA/NTSB) and is explicitly NOT BNSF-specific. The ROI figures are outputs of our own calculator at assumed inputs, not BNSF's actual economics, and must be re-run with BNSF's real numbers in the room.*
