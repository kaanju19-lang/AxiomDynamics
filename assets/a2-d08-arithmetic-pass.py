"""
A2 / D08 arithmetic pass — reproducible check.

Every figure in the A2 rate card and the D08 liability annex is recomputed here
from its stated source equation, then compared with the figure as written in the
document. Nothing is taken from memory; the expected values below are transcribed
from the files at the commit this script was written against.

Run:  python3 assets/a2-d08-arithmetic-pass.py
Exit: 0 if every checked figure matches, 1 if any does not.
"""

FAILURES = []
CHECKS = 0


def check(label, computed, stated, tol=0.5):
    """Compare a computed value to a figure as written in a document."""
    global CHECKS
    CHECKS += 1
    ok = abs(computed - stated) <= tol
    if not ok:
        FAILURES.append((label, computed, stated))
    print(f"{'PASS' if ok else 'FAIL'}  {label:<58} "
          f"computed {computed:>14,.2f}   stated {stated:>14,.2f}")
    return ok


# ---------------------------------------------------------------------------
# A2 §3.1 — marginal band rates
# ---------------------------------------------------------------------------
BAND1_RATE, BAND1_TOP = 600, 500
BAND2_RATE, BAND2_TOP = 500, 1_500          # next 1,500 axles (501-2,000)
BAND3_RATE = 375


def licence(axles):
    """Marginal band pricing: each band charges only for axles inside it."""
    b1 = min(axles, BAND1_TOP) * BAND1_RATE
    b2 = max(0, min(axles, 2_000) - BAND1_TOP) * BAND2_RATE
    b3 = max(0, axles - 2_000) * BAND3_RATE
    return b1 + b2 + b3


SITE_FEE = 45_000
PILOT_TOTAL = 370_000
PILOT_LICENCE = 180_000
CONVERSION_CREDIT = 0.50 * PILOT_LICENCE

# A1's default modelling assumptions, as built in build_roi_calculator.py
P_CAT = 0.0005                     # sheet 1, B17 (0.05%)
TYPICAL_FAILURE_COST = 500_000     # sheet 1, B14
CATASTROPHIC_FAILURE_COST = 1_000_000_000   # sheet 1, B18
COST_PER_MISSED = (1 - P_CAT) * TYPICAL_FAILURE_COST + P_CAT * CATASTROPHIC_FAILURE_COST
DEFECTS_CAUGHT = 2.1               # sheet 2, C7 per 500 axles
DEFECTS_LEGACY = 1.4               # sheet 2, B7 per 500 axles

print("\n=== A2 §3.1 band table ===")
check("Band 1 at top (500 x $600)", 500 * BAND1_RATE, 300_000)
check("Band 2 cumulative at 2,000", licence(2_000), 1_050_000)
check("Band 3 cumulative at 5,000", licence(5_000), 2_175_000)
check("Band 3 cumulative at 10,000", licence(10_000), 4_050_000)

print("\n=== A2 §3.3 worked examples ===")
# Example A - 500 axles, 1 site
check("Ex A licence subtotal (500 axles)", licence(500), 300_000)
check("Ex A annual total", licence(500) + 0, 300_000)
# Example B - 1,000 axles, 3 sites
check("Ex B licence subtotal (1,000 axles)", licence(1_000), 550_000)
check("Ex B site fee (2 x $45,000)", 2 * SITE_FEE, 90_000)
check("Ex B annual total", licence(1_000) + 2 * SITE_FEE, 640_000)
# Example C - 5,000 axles, 20 sites
check("Ex C licence subtotal (5,000 axles)", licence(5_000), 2_175_000)
check("Ex C site fee (19 x $45,000)", 19 * SITE_FEE, 855_000)
check("Ex C annual total", licence(5_000) + 19 * SITE_FEE, 3_030_000)

print("\n=== A2 §3.3 corridor site count ===")
check("2,200 mi at 64 mi spacing (lower bound)", 2_200 / 64, 34.4, tol=0.1)
check("2,200 mi at 40 mi spacing (upper bound)", 2_200 / 40, 55)
check("Site fees at 55 sites", 54 * SITE_FEE, 2_430_000)

print("\n=== A2 §5.1 pilot fee build-up ===")
components = {
    "Pilot licence": 180_000,
    "Implementation support": 65_000,
    "Training & certification": 40_000,
    "Validation support": 35_000,
    "Support during pilot": 50_000,
}
check("Pilot total fee", sum(components.values()), PILOT_TOTAL)
check("Payment 40% on signature", 0.40 * PILOT_TOTAL, 148_000)
check("Payment 30% at commissioning", 0.30 * PILOT_TOTAL, 111_000)
check("Payment 30% at month six", 0.30 * PILOT_TOTAL, 111_000)
check("Payments sum to total", 148_000 + 111_000 + 111_000, PILOT_TOTAL)
check("Conversion credit (50% of pilot licence)", CONVERSION_CREDIT, 90_000)

print("\n=== A2 §9 / D08 §5 rollover arithmetic ===")
check("Year 1 production licence (500 axles)", licence(500), 300_000)
y1_net = licence(500) - CONVERSION_CREDIT
check("Net Year 1 production fee", y1_net, 210_000)
three_yr = y1_net + 300_000 + 300_000
check("Three-year net total after conversion", three_yr, 810_000)
check("Four-year commitment incl. pilot", PILOT_TOTAL + three_yr, 1_180_000)

print("\n=== D08 §3.1 three-year cost table ===")
rows = [
    # label, axles, sites, stated licence, stated site fees, stated total, stated per-axle
    ("Single yard", 500, 1, 1_180_000, 0, 1_180_000, 2_360),
    ("Corridor, same axles", 500, 11, 1_180_000, 1_350_000, 2_530_000, 5_060),
    ("Thirteen divisions", 2_000, 13, 3_430_000, 1_620_000, 5_050_000, 2_525),
    ("Full division footprint", 5_000, 13, 6_805_000, 1_620_000, 8_425_000, 1_685),
]
for label, axles, sites, st_lic, st_site, st_tot, st_per in rows:
    band = licence(axles)
    comp_lic = PILOT_TOTAL + (band - CONVERSION_CREDIT) + band + band
    comp_site = SITE_FEE * (sites - 1) * 3
    comp_tot = comp_lic + comp_site
    check(f"{label}: 3-yr licence", comp_lic, st_lic)
    check(f"{label}: 3-yr site fees", comp_site, st_site)
    check(f"{label}: 3-yr total", comp_tot, st_tot)
    check(f"{label}: cost per axle", comp_tot / axles, st_per, tol=1)

print("\n=== D08 §3.1 the stated finding ===")
check("Corridor premium over single yard (%)",
      (2_530_000 / 1_180_000 - 1) * 100, 114, tol=1)
check("Unit cost ratio corridor/yard", 5_060 / 2_360, 2.144, tol=0.01)
check("Three-year charge per extra site", SITE_FEE * 3, 135_000)
check("Ten extra sites, three years", 10 * SITE_FEE * 3, 1_350_000)

print("\n=== D08 §4 performance component caps (33% of base) ===")
for axles, base, cap in ((500, 300_000, 99_000),
                         (1_000, 550_000, 181_500),
                         (2_000, 1_050_000, 346_500)):
    check(f"Cap at {axles:,} axles (33% of base)", 0.33 * licence(axles), cap)
    check(f"Base licence at {axles:,} axles", licence(axles), base)

print("\n=== D08 §4 worked example, 1,000 axles ===")
# Derived, not chosen: 1.4 missed defects per 1,000 axles at A1's $999,750.
PREVENTED_1K = 1.4 * COST_PER_MISSED
check("Prevented cost, 1.4 x A1 B22", PREVENTED_1K, 1_399_650)
check("3% of prevented cost", 0.03 * PREVENTED_1K, 41_989.50)
check("Payable (below the $181,500 cap)", min(0.03 * PREVENTED_1K, 0.33 * licence(1_000)), 41_989.50)
check("Total invoice", licence(1_000) + 0.03 * PREVENTED_1K, 591_989.50)
# The withdrawn round-number version, kept so the size of the drift is on record.
check("withdrawn $1,390,000 was this far below the model", PREVENTED_1K - 1_390_000, 9_650)

print("\n=== D08 §5 modelled returns (restated 2026-11-10 on A1) ===")
# A1's own arithmetic: 0.7 missed defects per 500 axles caught, each valued at
# A1 B22 = (1-0.0005)*500,000 + 0.0005*1,000,000,000, less 2.1 triggered
# inspections at $1,500 -- i.e. $1,393.35 net per axle per year.
A1_B22 = (1 - P_CAT) * TYPICAL_FAILURE_COST + P_CAT * CATASTROPHIC_FAILURE_COST


def a1_annual(axles):
    return (axles / 500) * (0.7 * A1_B22 - 2.1 * 1_500)


PILOT_AXLES = 200                 # D08 §2 scopes the pilot at 100-200 axles
BEN_PILOT = a1_annual(PILOT_AXLES)
BEN_PROD = a1_annual(500)

check("A1 B22 expected cost per missed defect", A1_B22, 999_750)
check("A1 net annual benefit at 500 axles", BEN_PROD, 696_675)
check("A1 net annual benefit at 200 axles (pilot)", BEN_PILOT, 278_670)
check("A1 net benefit per axle per year", a1_annual(500) / 500, 1_393.35, tol=0.05)
check("Pilot return, SAME fleet as §2 (0.75x)", BEN_PILOT / PILOT_TOTAL, 0.75, tol=0.005)
check("Pilot return at 100 axles (0.38x)", a1_annual(100) / PILOT_TOTAL, 0.38, tol=0.005)
# D08 §5: pilot at 200 axles, production at 500.
BEN_4YR = BEN_PILOT + 3 * BEN_PROD
BEN_6YR = BEN_PILOT + 5 * BEN_PROD
check("Four-year benefit (§5 table)", BEN_4YR, 2_368_695)
check("Four-year return (§5, 2.01x)", BEN_4YR / 1_180_000, 2.01, tol=0.005)
check("Six-year benefit (§6 table)", BEN_6YR, 3_762_045)
check("Six-year return (§6, 2.06x)", BEN_6YR / 1_825_750, 2.06, tol=0.005)
# §4 and §5 must value a prevented failure the same way. §4 states $1,390,000
# against 1.4 defects per 1,000 axles = $992,857; A1's B22 is $999,750.
check("§4 per-failure value, 1.4 defects per 1,000 axles", 1_390_000 / 1.4, 992_857, tol=1)
check("§4 as a share of A1 B22 (0.7% apart)", (1_390_000 / 1.4) / A1_B22, 0.993, tol=0.001)
# The pilot does NOT pay for itself at its own scoped fleet size. If a future
# edit makes it do so, either §2's scope or A1's inputs changed, and the claim
# in §5 that "the pilot does not pay for itself" would become false.
assert BEN_PILOT < PILOT_TOTAL, \
    "D08 §5 states the pilot does not pay for itself; at 200 axles A1 must not cover $370,000"
print("PASS  pilot benefit at §2's own fleet size is below the pilot fee (0.75x)")

print("\n=== D08 §6 CapEx/OpEx cumulative ===")
cum = 0
for label, fee, stated_cum in (("Y1 pilot", 370_000, 370_000),
                               ("Y2 production Y1", 210_000, 580_000),
                               ("Y3 production Y2", 300_000, 880_000),
                               ("Y4 production Y3", 300_000, 1_180_000)):
    cum += fee
    check(f"Cumulative through {label}", cum, stated_cum)

print("\n=== D08 §6 five-year extension (max +5%/yr from Year 4) ===")
y5 = 300_000 * 1.05
y6 = y5 * 1.05
check("Y5 at max +5%", y5, 315_000)
check("Y6 at max +5%", y6, 330_750)
check("Cumulative through Y5", 1_180_000 + y5, 1_495_000)
check("Cumulative through Y6", 1_180_000 + y5 + y6, 1_825_750)
check("Six-year customer commitment (§6)", 1_180_000 + y5 + y6, 1_825_750)

print("\n=== D08 §6 six-year modelled benefit and return (restated 2026-11-10) ===")
six_yr = 1_180_000 + y5 + y6
check("Six-year benefit, pilot at 200 + 5 yrs at 500", BEN_6YR, 3_762_045)
check("Cumulative benefit through year 5", BEN_PILOT + 4 * BEN_PROD, 3_065_370)
check("Six-year return (2.06x)", BEN_6YR / six_yr, 2.06, tol=0.005)
# Two effects nearly cancel: the fee escalates from Year 4, which drags the
# multiple down, while one weak pilot year diluted across more production years
# lifts it. The multiple rises, but only slightly -- not a growth story.
assert BEN_6YR / six_yr > BEN_4YR / 1_180_000, \
    "six-year multiple should exceed four-year: one weak pilot year diluted across more production years"
assert BEN_6YR / six_yr - BEN_4YR / 1_180_000 < 0.10, \
    "six-year multiple should exceed the four-year one only marginally: fee escalation offsets the gain"
print("PASS  six-year multiple exceeds four-year only marginally (pilot dilution vs fee escalation)")

print("\n=== D08 §6 / D06 §6 thirteen-site, 2,000-axle quote ===")
check("Annual licence at 2,000 axles", licence(2_000), 1_050_000)
check("Site fees, 12 additional", 12 * SITE_FEE, 540_000)
check("Combined annual", licence(2_000) + 12 * SITE_FEE, 1_590_000)
check("D06 quarterly platform fee", (licence(2_000) + 12 * SITE_FEE) / 4, 397_500)
check("D06 5% credit on quarterly fee", 0.05 * 397_500, 19_875)

print("\n=== A1 as-built (the workbook on disk) — the numbers the instrument actually produces ===")
# Sheet 4 now charges A2 §5.1's full $370,000 pilot (licence 180k + implementation
# 65k + training/validation/support 125k), not the old $285,000 that omitted two
# A2 lines. Sheet 5's three-year cost is therefore 370,000 + 2 x 320,994.75.
check("A1 three-year net benefit", 3 * a1_annual(500), 2_090_025)
A1_3YR_COST = 370_000 + 2 * (300_000 + 20_994.75)
check("A1 three-year cost, pilot 370k + 2 production years", A1_3YR_COST, 1_011_989.50, tol=1)
check("A1 three-year ROI", 3 * a1_annual(500) / A1_3YR_COST, 2.0653, tol=0.001)
check("A1 year-2 cost per monitored axle", (300_000 + 20_994.75) / 500, 641.99, tol=0.01)
check("A1 pilot payback, months", 370_000 / a1_annual(500) * 12, 6.37, tol=0.01)

print("\n=== FINDING 1 — CLOSED 2026-11-10. A2 §3.2 / D08 §3 anchors restated on A1 ===")
# The documents previously claimed "approximately 2.0x at 500 axles, rising to
# about 4.1x at 10,000". Neither basis reproduces that pair, which is what made
# it a finding. The owner decided A1 governs; both documents now state the
# A2-basis column below.

def benefit_3yr(axles):
    detected = (axles / 500) * DEFECTS_CAUGHT
    missed = (axles / 500) * (DEFECTS_CAUGHT - DEFECTS_LEGACY)
    return 3 * (missed * COST_PER_MISSED - detected * 1_500)


def cost_a2_basis(axles):
    b = licence(axles)
    return PILOT_TOTAL + (b - CONVERSION_CREDIT) + b + b


def cost_a1_basis(axles):
    b = licence(axles)
    return 285_000 + b + b          # A1 Y1 pilot $285k, no conversion credit, no site fee


print(f"      cost per missed defect (A1 B22) = ${COST_PER_MISSED:,.0f}")
for axles in (500, 1_000, 2_000, 5_000, 10_000):
    print(f"      {axles:>6,} axles  benefit ${benefit_3yr(axles):>12,.0f}   "
          f"A2-basis {benefit_3yr(axles)/cost_a2_basis(axles):>5.2f}x   "
          f"A1-basis {benefit_3yr(axles)/cost_a1_basis(axles):>5.2f}x")
check("Anchor 1, A2 basis at 500 axles (A2 §3.2, D08 §3)",
      benefit_3yr(500) / cost_a2_basis(500), 1.77, tol=0.005)
check("Anchor 2, A2 basis at 10,000 axles (A2 §3.2, D08 §3)",
      benefit_3yr(10_000) / cost_a2_basis(10_000), 3.36, tol=0.005)
# The same pair on a basis that ALSO disallows the conversion credit. A2 §3.2
# states these as the fallback, so they must stay true too.
def cost_list_no_credit(axles):
    return PILOT_TOTAL + 3 * licence(axles)

check("A2 §3.2 fallback at 500, no conversion credit (1.65x)",
      benefit_3yr(500) / cost_list_no_credit(500), 1.65, tol=0.005)
check("A2 §3.2 fallback at 10,000, no conversion credit (3.34x)",
      benefit_3yr(10_000) / cost_list_no_credit(10_000), 3.34, tol=0.005)
print("      The withdrawn 2.0x/4.1x pair is not reproducible on any basis in this repo.")
print("      -> CLOSED: replaced by the pair checked above, which the documents state.")

print("\n=== FINDING 2 — CLOSED 2026-11-10. D08 §5/§6 restated on A1 ===")
# The withdrawn figures, kept so the size of the correction stays on record.
print(f"      A1 annual benefit at 500 axles        ${696_675:>12,}")
print(f"      withdrawn: §5 pilot year $6M-$8M      ratio {6e6/696_675:>5.1f}x - {8e6/696_675:>5.1f}x")
print(f"      withdrawn: §5 four years $14M-$20M    ratio {14e6/(4*696_675):>5.1f}x - {20e6/(4*696_675):>5.1f}x")
print(f"      withdrawn: §6 six years $40M-$60M     ratio {40e6/(6*696_675):>5.1f}x - {60e6/(6*696_675):>5.1f}x")
# The restated figures, ASSERTED against the prose -- not printed as fact. An
# earlier version of this block printed stale 500-axles-every-year values under
# the word "restated" and checked nothing; both were $418,005 high, exactly one
# pilot-year benefit (696,675 - 278,670).
check("restated: §5 pilot year (200 axles)", BEN_PILOT, 278_670)
check("restated: §5 four years", BEN_4YR, 2_368_695)
check("restated: §6 six years", BEN_6YR, 3_762_045)
print("      -> CLOSED: the three checks immediately above verify §5 and §6.")

print("\n" + "=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} of {CHECKS} checks FAILED:")
    for label, computed, stated in FAILURES:
        print(f"  - {label}: computed {computed:,.2f}, document says {stated:,.2f}")
    raise SystemExit(1)
print(f"All {CHECKS} checks passed.")
print("Findings 1 and 2 are CLOSED as of 2026-11-10; both are checked above, not merely recorded.")

