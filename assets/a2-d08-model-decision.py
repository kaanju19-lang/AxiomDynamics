"""
A2 / D08 model decision — reproducible check.

Every figure quoted in `assets/a2-d08-model-decision-2026-11-09.md` is
recomputed here from its stated source equation. Nothing is transcribed from the
document; if a number in the paper stops matching this script, the paper is
wrong and this script says so.

This is a companion to `a2-d08-arithmetic-pass.py`, which checks that A2 and D08
are internally arithmetically correct. That script answers "do the figures add
up?" This one answers "which model produced them, and can it be recovered?"

Run:  python3 -I assets/a2-d08-model-decision.py
Exit: 0 if every figure reproduces, 1 if any does not.
"""

FAILURES = []
CHECKS = 0


def check(label, computed, stated, tol=0.01):
    """Compare a computed value to the figure stated in the decision paper."""
    global CHECKS
    CHECKS += 1
    ok = abs(computed - stated) <= tol
    if not ok:
        FAILURES.append((label, computed, stated))
    unit = "x" if label.endswith("x") else ""
    print(f"{'PASS' if ok else 'FAIL'}  {label:<62} "
          f"computed {computed:>14,.4f}   paper {stated:>14,.4f}")
    return ok


# ---------------------------------------------------------------------------
# The model, as A1 builds it. These constants are A1's default cells.
# ---------------------------------------------------------------------------
B14_TYPICAL = 500_000            # A1 sheet 1, B14 — typical contained derailment cost
B18_CATASTROPHIC = 1_000_000_000  # A1 sheet 1, B18 — East Palestine, cumulative
P_A1 = 0.0005                    # A1 sheet 1, B17 — 0.05%
P_ROI = 0.02                     # backend/roi.py — 2%

DEFECTS_AXIOM = 2.1              # A1 sheet 2, C7 per 500 axles per year
DEFECTS_LEGACY = 1.4             # A1 sheet 2, B7 per 500 axles per year
MISSED_PER_500 = DEFECTS_AXIOM - DEFECTS_LEGACY          # 0.7
COST_PER_FALSE_ALARM = 1_500     # A1 sheet 3, row 10

PILOT_TOTAL = 370_000            # A2 §5.1
PILOT_CREDIT = 90_000            # A2 §5.1, 50% of the $180,000 pilot licence
A1_PILOT = 285_000               # A1 sheet 4, as built — not the $370,000 A2 charges


def cost_per_missed(p):
    """A1 B22: (1 - p) * typical + p * catastrophic."""
    return (1 - p) * B14_TYPICAL + p * B18_CATASTROPHIC


def licence(axles):
    """A2 §3.1 marginal bands: each band charges only for axles inside it."""
    b1 = min(axles, 500) * 600
    b2 = max(0, min(axles, 2_000) - 500) * 500
    b3 = max(0, axles - 2_000) * 375
    return b1 + b2 + b3


def annual_benefit(axles, p):
    """A1 sheet 3 rows 6-11: prevented cost less false-alarm cost, one year."""
    detected = (axles / 500) * DEFECTS_AXIOM
    saved = (axles / 500) * MISSED_PER_500 * cost_per_missed(p)
    return saved - detected * COST_PER_FALSE_ALARM


def benefit_3yr(axles, p):
    return 3 * annual_benefit(axles, p)


print("\n=== §3  Finding 1 — the anchors, recovered ===")
print(f"      p = 0.05%  -> cost per missed defect ${cost_per_missed(P_A1):,.0f}")
print(f"      p = 2%     -> cost per missed defect ${cost_per_missed(P_ROI):,.0f}")
print()
print("      Requirement from the two anchors (benefit is linear in axles):")
print("        r(10,000)/r(500) = 20 * cost(500)/cost(10,000) = 4.1/2.0 = 2.05")
print("        therefore cost(10,000)/cost(500) = 20/2.05 = 9.756")
check("Required cost ratio (20 / 2.05)", 20 / 2.05, 9.756, tol=0.001)

bases = {
    "Pilot + 3 full yrs, no credit": lambda a: PILOT_TOTAL + 3 * licence(a),
    "Pilot + 3 yrs, with credit": lambda a: PILOT_TOTAL - PILOT_CREDIT + 3 * licence(a),
    "A1 as-built ($285k + 2 yrs)": lambda a: A1_PILOT + 2 * licence(a),
    "Three production years only": lambda a: 3 * licence(a),
}
def p_for_anchor(cost, axles, target):
    """The catastrophic probability at which this cost basis hits one anchor.

    benefit_3yr(axles, p) = 3 * (axles/500) * (0.7*C - 2.1*1500), C = (1-p)*B14 + p*B18
    Setting that equal to target * cost(axles) and solving for C, then p:
        3 * (axles/500) * (0.7*C - 3150) = target * cost(axles)
        0.7*C = target * cost(axles) / (3 * axles/500) + 3150
    """
    scale = axles / 500
    c_eq = target * cost(axles) / (3 * scale) + DEFECTS_AXIOM * COST_PER_FALSE_ALARM
    C = c_eq / MISSED_PER_500
    return (C - B14_TYPICAL) / (B18_CATASTROPHIC - B14_TYPICAL)


REQUIRED_RATIO = 20 / 2.05       # 9.756 — what the two anchors jointly demand

print(f"\n      {'basis':32s} {'cost(500)':>12s} {'cost(10k)':>13s} {'ratio':>7s} "
      f"{'vs 9.756':>9s} {'p@2.0x':>10s} {'p@4.1x':>10s} {'spread':>8s}")
table = {}
for name, cost in bases.items():
    c5, c10 = cost(500), cost(10_000)
    p2 = p_for_anchor(cost, 500, 2.0)
    p41 = p_for_anchor(cost, 10_000, 4.1)
    dev = 100 * (c10 / c5 - REQUIRED_RATIO) / REQUIRED_RATIO
    spread = 100 * (p41 - p2) / p2
    table[name] = (c10 / c5, dev, p2, p41, spread)
    print(f"      {name:32s} {c5:>12,.0f} {c10:>13,.0f} {c10/c5:>7.3f} "
          f"{dev:>+8.1f}% {100*p2:>9.4f}% {100*p41:>9.4f}% {spread:>+7.1f}%")

print("\n      The paper's table gives, in this column order:")
check("ratio, pilot + 3 yrs no credit (paper 9.86)", table['Pilot + 3 full yrs, no credit'][0], 9.86, tol=0.005)
check("  deviation from required ratio (paper +1.0%)", table['Pilot + 3 full yrs, no credit'][1], 1.0, tol=0.1)
check("  p@2.0x (paper 0.0714%)", 100*table['Pilot + 3 full yrs, no credit'][2], 0.0714, tol=0.0001)
check("  p@4.1x (paper 0.0727%)", 100*table['Pilot + 3 full yrs, no credit'][3], 0.0727, tol=0.0001)
check("  spread between the two (paper +1.8%)", table['Pilot + 3 full yrs, no credit'][4], 1.8, tol=0.1)

check("ratio, pilot + 3 yrs with credit (paper 10.53)", table['Pilot + 3 yrs, with credit'][0], 10.53, tol=0.01)
check("  deviation from required ratio (paper +8.0%)", table['Pilot + 3 yrs, with credit'][1], 8.0, tol=0.2)
check("  spread between the two (paper +14.3%)", table['Pilot + 3 yrs, with credit'][4], 14.3, tol=0.3)

check("ratio, A1 as-built (paper 9.47)", table['A1 as-built ($285k + 2 yrs)'][0], 9.47, tol=0.01)
check("  deviation from required ratio (paper -2.9%)", table['A1 as-built ($285k + 2 yrs)'][1], -2.9, tol=0.2)
check("  spread between the two (paper -7.0%)", table['A1 as-built ($285k + 2 yrs)'][4], -7.0, tol=0.3)

check("ratio, production only (paper 13.50)", table['Three production years only'][0], 13.50, tol=0.01)
check("  deviation from required ratio (paper +38.4%)", table['Three production years only'][1], 38.4, tol=0.5)
check("  spread between the two (paper +91%)", table['Three production years only'][4], 91.0, tol=1.5)

# The recovered parameter and what it produces
COST = bases["Pilot + 3 full yrs, no credit"]
c5, c10 = COST(500), COST(10_000)
p_rec = p_for_anchor(COST, 500, 2.0)
print(f"\n      recovered p on that basis = {100*p_rec:.4f}%  (paper says 0.0714%)")
check("recovered p, percent (paper 0.0714)", 100 * p_rec, 0.0714, tol=0.0002)
check("  -> return at 500 axles (paper 2.00x)", benefit_3yr(500, p_rec) / c5, 2.00, tol=0.01)
check("  -> return at 10,000 axles (paper 4.06x)", benefit_3yr(10_000, p_rec) / c10, 4.06, tol=0.01)
check("cost ratio on the recovered basis (paper 9.86)", c10 / c5, 9.86, tol=0.01)

print("\n      The horizon is not unique — this is why Finding 1 stays open:")
# Same basis, but pair four years of benefit with the four-year cost.
for horizon in (3, 4):
    c_eq5 = 2.0 * c5 / (horizon * (500 / 500)) + DEFECTS_AXIOM * COST_PER_FALSE_ALARM
    c_eq10 = 4.1 * c10 / (horizon * (10_000 / 500)) + DEFECTS_AXIOM * COST_PER_FALSE_ALARM
    p5 = (c_eq5 / MISSED_PER_500 - B14_TYPICAL) / (B18_CATASTROPHIC - B14_TYPICAL)
    p10 = (c_eq10 / MISSED_PER_500 - B14_TYPICAL) / (B18_CATASTROPHIC - B14_TYPICAL)
    print(f"      {horizon}-year benefit horizon: p = {100*p5:.4f}% / {100*p10:.4f}%  "
          f"spread {100*(p10-p5)/p5:+.1f}%")

four_yr_p = None
c_eq5 = 2.0 * c5 / (4 * 1) + DEFECTS_AXIOM * COST_PER_FALSE_ALARM
four_yr_p = (c_eq5 / MISSED_PER_500 - B14_TYPICAL) / (B18_CATASTROPHIC - B14_TYPICAL)
check("4-year horizon also fits anchor 1 (paper 0.0412%)", 100 * four_yr_p, 0.0412, tol=0.0002)

print("\n=== §3  three defensible frames for 'return' at 500 axles ===")
# These are the three frames the paper cites in reason 3. The anchor matches none.
bd500 = benefit_3yr(500, P_A1)
check("annual basis: benefit / $300,000 licence (paper 2.32x)",
      annual_benefit(500, P_A1) / licence(500), 2.32, tol=0.005)
check("3-yr benefit / 3-yr fee excl. pilot, $810,000 (paper 2.58x)",
      bd500 / ((licence(500) - PILOT_CREDIT) + 2 * licence(500)),
      2.58, tol=0.005)
check("3-yr benefit / 4-yr commitment, $1,180,000 (paper 1.77x)",
      bd500 / 1_180_000, 1.77, tol=0.005)

print("\n=== §4.1  D08 contradicts itself, independent of A1 ===")
# §4: 1,000 axles, corroborated prevented cost $1,390,000
missed_1k = (1_000 / 500) * MISSED_PER_500
value_sec4 = 1_390_000 / missed_1k
check("§4 value per prevented failure (paper $992,857)", value_sec4, 992_857, tol=1)
check("§5 low value per prevented failure (paper $8,571,429)", 6_000_000 / 0.7, 8_571_429, tol=1)
check("§5 high value per prevented failure (paper $11,428,571)", 8_000_000 / 0.7, 11_428_571, tol=1)
check("§5/§4 ratio, low (paper 8.6x)", (6_000_000 / 0.7) / value_sec4, 8.6, tol=0.05)
check("§5/§4 ratio, high (paper 11.5x)", (8_000_000 / 0.7) / value_sec4, 11.5, tol=0.05)

print("\n=== §4.2  the three periods do not reconcile ===")
periods = {
    "low": dict(pilot=6e6, four=14e6, six=40e6),
    "high": dict(pilot=8e6, four=20e6, six=60e6),
}
for case, d in periods.items():
    y2_4 = (d["four"] - d["pilot"]) / 3
    y5_6 = (d["six"] - d["four"]) / 2
    print(f"      {case:4s}  years 2-4 ${y2_4/1e6:>5.2f}M/yr = {100*y2_4/d['pilot']:>5.0f}% of pilot   "
          f"years 5-6 ${y5_6/1e6:>5.2f}M/yr = {100*y5_6/d['pilot']:>5.0f}% of pilot")
check("low case, years 2-4 share of pilot (paper 44%)",
      100 * ((14e6 - 6e6) / 3) / 6e6, 44.0, tol=1.0)
check("high case, years 2-4 share of pilot (paper 50%)",
      100 * ((20e6 - 8e6) / 3) / 8e6, 50.0, tol=1.0)
check("low case, years 5-6 share of pilot (paper 217%)",
      100 * ((40e6 - 14e6) / 2) / 6e6, 217.0, tol=2.0)
check("high case, years 5-6 share of pilot (paper 250%)",
      100 * ((60e6 - 20e6) / 2) / 8e6, 250.0, tol=2.0)

print("\n=== §4.3  A1's outputs and the restated returns ===")
check("A1 net annual benefit at 500 axles (paper $696,675)", annual_benefit(500, P_A1), 696_675, tol=1)
check("  against the $370,000 pilot fee (paper 1.88x)",
      annual_benefit(500, P_A1) / PILOT_TOTAL, 1.88, tol=0.01)
check("A1 four-year benefit (paper $2,786,700)", 4 * annual_benefit(500, P_A1), 2_786_700, tol=2)
check("  against the $1,180,000 commitment (paper 2.36x)",
      4 * annual_benefit(500, P_A1) / 1_180_000, 2.36, tol=0.01)
check("A1 six-year benefit (paper $4,180,050)", 6 * annual_benefit(500, P_A1), 4_180_050, tol=3)
check("  against the $1,825,750 commitment (paper 2.29x)",
      6 * annual_benefit(500, P_A1) / 1_825_750, 2.29, tol=0.01)

print("\n      D08's stated returns, recomputed from its own figures:")
check("pilot return low, 6M/370k (paper 16.2x)", 6e6 / PILOT_TOTAL, 16.2, tol=0.05)
check("pilot return high, 8M/370k (paper 21.6x)", 8e6 / PILOT_TOTAL, 21.6, tol=0.05)
check("four-year low, 14M/1.18M (paper 11.9x)", 14e6 / 1_180_000, 11.9, tol=0.05)
check("six-year low, 40M/1.82575M (paper 21.9x)", 40e6 / 1_825_750, 21.9, tol=0.05)
check("six-year high, 60M/1.82575M (paper 32.9x)", 60e6 / 1_825_750, 32.9, tol=0.05)

print("\n=== §4.4  the dashboard versus the workbook ===")
# roi.py has NO axle input -- it takes warrants. So there is no "at 500 axles"
# figure for it. The correct like-for-like comparison is per-defect valuation.
CONTAINED_MIDPOINT = (5_000_000 + 13_500_000) / 2      # roi.py: $9.25M
roi_p = 0.02
roi_cost = (1 - roi_p) * CONTAINED_MIDPOINT + roi_p * B18_CATASTROPHIC
check("roi.py per-missed-defect value (paper $29,065,000)", roi_cost, 29_065_000, tol=1)
check("  ratio to A1's $999,750 (paper 29.1x)", roi_cost / cost_per_missed(P_A1), 29.1, tol=0.05)
check("A1's contained cost at roi.py's 2%, for decomposition (paper $20,490,000)",
      cost_per_missed(P_ROI), 20_490_000, tol=1)
check("  that alone is this multiple of A1 (paper 20.5x)",
      cost_per_missed(P_ROI) / cost_per_missed(P_A1), 20.5, tol=0.05)
check("roi.py's basis at A1's 0.05% (paper $9,745,375)",
      (1 - P_A1) * CONTAINED_MIDPOINT + P_A1 * B18_CATASTROPHIC, 9_745_375, tol=1)

print("\n=== §5  the anchors under the recommendation ===")
cost4 = lambda a: PILOT_TOTAL + (licence(a) - PILOT_CREDIT) + 2 * licence(a)
rows = [(500, 2_090_025, 1_180_000, 1.77),
        (1_000, 4_180_050, 1_930_000, 2.17),
        (2_000, 8_360_100, 3_430_000, 2.44),
        (5_000, 20_900_250, 6_805_000, 3.07),
        (10_000, 41_800_500, 12_430_000, 3.36)]
for axles, st_ben, st_cost, st_ret in rows:
    check(f"benefit at {axles:,} axles (paper ${st_ben:,})", benefit_3yr(axles, P_A1), st_ben, tol=3)
    check(f"  four-year commitment at {axles:,} (paper ${st_cost:,})", cost4(axles), st_cost, tol=1)
    check(f"  return at {axles:,} (paper {st_ret}x)", benefit_3yr(axles, P_A1) / cost4(axles), st_ret, tol=0.01)

print("\n=== §6  the implied p behind each option ===")
for label, benefit in (("§5 low, $6M pilot year", 6e6), ("§5 high, $8M pilot year", 8e6)):
    c = (benefit + DEFECTS_AXIOM * COST_PER_FALSE_ALARM) / (MISSED_PER_500 * 1)
    p = (c - B14_TYPICAL) / (B18_CATASTROPHIC - B14_TYPICAL)
    print(f"      {label:28s} implies p = {100*p:.3f}%")
check("p implied by $6M pilot year (paper ~0.8%)",
      100 * (((6e6 + DEFECTS_AXIOM * COST_PER_FALSE_ALARM) / MISSED_PER_500 - B14_TYPICAL)
             / (B18_CATASTROPHIC - B14_TYPICAL)), 0.81, tol=0.02)
check("p implied by $8M pilot year (paper ~1.1%)",
      100 * (((8e6 + DEFECTS_AXIOM * COST_PER_FALSE_ALARM) / MISSED_PER_500 - B14_TYPICAL)
             / (B18_CATASTROPHIC - B14_TYPICAL)), 1.09, tol=0.02)

print("\n" + "=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} of {CHECKS} checks FAILED:")
    for label, computed, stated in FAILURES:
        print(f"  - {label}: computed {computed:,.4f}, paper says {stated:,.4f}")
    raise SystemExit(1)
print(f"All {CHECKS} checks passed. Every figure in the decision paper reproduces.")
