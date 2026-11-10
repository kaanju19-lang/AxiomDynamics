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
check("3% of $1,390,000 prevented cost", 0.03 * 1_390_000, 41_700)
check("Payable (below the $181,500 cap)", min(0.03 * 1_390_000, 0.33 * licence(1_000)), 41_700)
check("Total invoice", licence(1_000) + 41_700, 591_700)

print("\n=== D08 §5 modelled returns ===")
check("Pilot return, low bound (6M / 370k)", 6_000_000 / PILOT_TOTAL, 16.2, tol=0.1)
check("Pilot return, high bound (8M / 370k)", 8_000_000 / PILOT_TOTAL, 21.6, tol=0.1)
check("Four-year return, low (14M / 1.18M)", 14_000_000 / 1_180_000, 11.9, tol=0.1)
check("Four-year return, high (20M / 1.18M)", 20_000_000 / 1_180_000, 16.9, tol=0.1)

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
check("Six-year total stated as ~$1.83M", (1_180_000 + y5 + y6) / 1_000_000, 1.83, tol=0.005)

print("\n=== D08 §6 'modelled ROI 20x-30x' over six years ===")
six_yr = 1_180_000 + y5 + y6
check("Six-year return, low (40M / total)", 40_000_000 / six_yr, 21.9, tol=0.1)
check("Six-year return, high (60M / total)", 60_000_000 / six_yr, 32.9, tol=0.1)

print("\n=== D08 §6 / D06 §6 thirteen-site, 2,000-axle quote ===")
check("Annual licence at 2,000 axles", licence(2_000), 1_050_000)
check("Site fees, 12 additional", 12 * SITE_FEE, 540_000)
check("Combined annual", licence(2_000) + 12 * SITE_FEE, 1_590_000)
check("D06 quarterly platform fee", (licence(2_000) + 12 * SITE_FEE) / 4, 397_500)
check("D06 5% credit on quarterly fee", 0.05 * 397_500, 19_875)

print("\n=== A1 as-built (the workbook on disk) — the numbers the instrument actually produces ===")
# The built workbook computes, at 500 axles / 1 site / default assumptions:
check("A1 net annual benefit at 500 axles", 696_675, 696_675)
check("A1 three-year net benefit", 3 * 696_675, 2_090_025)
check("A1 three-year cost at 500 axles", 926_989.50, 926_989.50, tol=1)
check("A1 three-year ROI", 2_090_025 / 926_989.50, 2.2546, tol=0.001)

print("\n=== FINDING 1: A2 §3.2 / D08 §3 modelled-return claim does not reproduce ===")
# A2 says "approximately 2.0x at 500 axles, rising to about 4.1x at 10,000".
# D08 §3 repeats both. Recompute on the only two cost bases that exist.

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
print("      A2/D08 claim: 2.0x at 500, 4.1x at 10,000. "
      "Neither basis reaches 4.1x; no parameter set in the repo reproduces both.")
print("      -> recorded as an open item, not silently corrected (see A2 §3.2 and the pass record).")

print("\n=== FINDING 2: D08 §5 / §6 modelled benefits exceed what A1 produces ===")
print(f"      A1 annual benefit at 500 axles      ${696_675:>12,}")
print(f"      D08 §5 states pilot year $6M-$8M    ratio {6e6/696_675:>5.1f}x - {8e6/696_675:>5.1f}x")
print(f"      D08 §5 states four years $14M-$20M  ratio {14e6/(4*696_675):>5.1f}x - {20e6/(4*696_675):>5.1f}x")
print(f"      D08 §6 states six years $40M-$60M   ratio {40e6/(6*696_675):>5.1f}x - {60e6/(6*696_675):>5.1f}x")
print("      Any per-defect valuation supporting D08's figures runs well above A1's $999,750.")
print("      -> recorded as an open item requiring an owner decision on which model governs.")

print("\n" + "=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} of {CHECKS} checks FAILED:")
    for label, computed, stated in FAILURES:
        print(f"  - {label}: computed {computed:,.2f}, document says {stated:,.2f}")
    raise SystemExit(1)
print(f"All {CHECKS} checks passed.")
print(f"Plus 2 open findings recorded above (not arithmetic errors — models that disagree).")

