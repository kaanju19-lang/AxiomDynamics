"""
Business ROI / cost-avoidance math.

This module draws a hard line between two kinds of numbers:

  REAL, SOURCED figures -- documented dollar costs from actual bearing-
  failure-related derailments, cited to NTSB and DOJ/EPA records. These
  are not guesses.

  MODELING ASSUMPTIONS -- things nobody has published (there is no
  public, standardized "base rate" for what fraction of bearing failures
  go catastrophic vs. stay contained; no public per-pilot inspection cost
  for THIS product specifically). These are clearly labeled as
  assumptions you should replace with your own figures or your pilot
  customer's figures before this supports a real business case.

Mixing those two categories without labeling them would be the single
most misleading thing this app could do, so every number below says which
category it's in.

---------------------------------------------------------------------
SOURCED FIGURES -- bearing/wheelset-failure-related derailment cost
---------------------------------------------------------------------

Tier 1 -- CONTAINED bearing/wheelset failure (no hazmat release):
  - BNSF bearing-related derailment: $5,000,000 reported damage.
    Source: NTSB, https://www.ntsb.gov/investigations/accidentreports/reports/rab1712.pdf
  - Separate BNSF derailment: $13,500,000 reported damage, EXPLICITLY
    excluding lading and environmental remediation costs.
    Source: NTSB docket, https://data.ntsb.gov/Docket/Document/docBLOB?FileExtension=.PDF&FileName=BNSF%20Equipment%20Incident%20Report-Redacted.PDF&ID=40457595
  These two figures bracket the "contained" tier used below ($5M-$13.5M).
  No published, standardized FRA-wide average derailment cost exists --
  FRA tracks accident counts/causes, not a normalized dollar average --
  so this range, not a single average, is what the model uses.

Tier 2 -- CATASTROPHIC failure with hazmat release (East Palestine, OH,
Feb 3 2023, Norfolk Southern train 32N -- a wheel bearing failure, the
exact failure mode this product targets, though NS not BNSF):
  - $310,000,000+ federal settlement (EPA/DOJ: ~$235M cleanup, $15M Clean
    Water Act penalty, $30M water monitoring, $25M health fund, etc.)
    Source: DOJ, https://www.justice.gov/opa/pr/united-states-reaches-over-310-million-settlement-norfolk-southern-address-harms-caused-east
  - $600,000,000 personal-injury class settlement, paid fully by Norfolk
    Southern after co-defendants GATX/OxyVinyls were found not liable.
    Source: AP, https://apnews.com/article/east-palestine-derailment-norfolk-southern-gatx-oxyvinyls-2d5110bf096ec3524f3092999bee3060
  - Cumulative cost to Norfolk Southern reported to have exceeded $1
    billion by mid-2024.
    Source: https://www.kten.com/story/49275631/east-palestine-train-derailment-has-now-cost-norfolk-southern-1-billion

---------------------------------------------------------------------
MODELING ASSUMPTIONS (replace before real use)
---------------------------------------------------------------------
  - P_CATASTROPHIC_GIVEN_MISSED_DEFECT: no public base rate exists for
    "what fraction of missed/undetected bearing defects progress to a
    catastrophic hazmat-release event vs. stay a contained derailment."
    Set conservatively low here (2%) -- East Palestine-scale events are
    rare tail outcomes, not the typical case, but the downside is so
    large it still dominates expected cost. REPLACE with your own risk
    estimate or your pilot customer's safety data if you have one.
  - COST_PROACTIVE_INSPECTION_USD / COST_UNCORROBORATED_FALSE_ALARM_USD:
    illustrative placeholders for what it costs to act on a warrant --
    use your own maintenance/inspection cost data.
  - LEGACY/AXIOM_MEAN_TIME_TO_DETECT_HOURS: illustrative, not measured.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

# ---------------------------------------------------------------------------
# SOURCED: contained-failure cost range (see citations above)
# ---------------------------------------------------------------------------
CONTAINED_FAILURE_COST_LOW_USD = 5_000_000
CONTAINED_FAILURE_COST_HIGH_USD = 13_500_000
CONTAINED_FAILURE_COST_USD = (CONTAINED_FAILURE_COST_LOW_USD + CONTAINED_FAILURE_COST_HIGH_USD) / 2  # midpoint, $9.25M

# ---------------------------------------------------------------------------
# SOURCED: catastrophic-failure cost (East Palestine, OH, Feb 3 2023)
# ---------------------------------------------------------------------------
CATASTROPHIC_FAILURE_COST_USD = 1_000_000_000  # cumulative cost reported at NS, see citation above

# ---------------------------------------------------------------------------
# ASSUMPTION: probability a missed defect goes catastrophic rather than
# contained. NOT a published base rate -- see note above. Replace with a
# real risk estimate before using this for an actual business case.
# ---------------------------------------------------------------------------
P_CATASTROPHIC_GIVEN_MISSED_DEFECT = 0.02

# Expected cost of ONE missed/undetected bearing defect that this system
# would have corroborated and flagged -- a probability-weighted blend of
# the two sourced tiers above, not a single invented number.
EXPECTED_COST_PER_MISSED_DEFECT_USD = (
    (1 - P_CATASTROPHIC_GIVEN_MISSED_DEFECT) * CONTAINED_FAILURE_COST_USD
    + P_CATASTROPHIC_GIVEN_MISSED_DEFECT * CATASTROPHIC_FAILURE_COST_USD
)

# ---------------------------------------------------------------------------
# ASSUMPTION: cost to act on a warrant (not sourced -- use your own figures)
# ---------------------------------------------------------------------------
COST_UNCORROBORATED_FALSE_ALARM_USD = 1_200    # cost of inspecting a single-signal REVIEW that turns out clean
COST_PROACTIVE_INSPECTION_USD = 4_500          # cost of a planned inspection triggered by an URGENT REVIEW

# ---------------------------------------------------------------------------
# ASSUMPTION: detection-time comparison (illustrative, not measured)
# ---------------------------------------------------------------------------
LEGACY_MEAN_TIME_TO_DETECT_HOURS = 4.8
AXIOM_MEAN_TIME_TO_DETECT_HOURS = 0.57


@dataclass
class ROISummary:
    fleet_size: int
    mission_ready_pct: float
    urgent_review_count: int
    review_count: int
    estimated_failures_avoided: int
    expected_cost_per_missed_defect_usd: float
    estimated_cost_avoided_usd: float
    estimated_inspection_cost_usd: float
    net_estimated_benefit_usd: float
    legacy_mttd_hours: float
    axiom_mttd_hours: float
    mttd_improvement_pct: float
    contained_cost_range_usd: tuple
    catastrophic_cost_usd: float
    catastrophic_probability_assumption: float
    assumptions_note: str
    sourced_note: str


def compute_roi_summary(warrants: List) -> ROISummary:
    """
    `warrants` is the list of GhostWarrant objects from warrants.py for
    the current fleet snapshot (same objects /api/alerts returns).

    Logic (not the dollar inputs) is the defensible part:
      - A CORROBORATED URGENT REVIEW represents a defect two independent
        physical signals agree on -- in this framework, that's the case
        we count as "a failure this system plausibly prevented," costed
        at EXPECTED_COST_PER_MISSED_DEFECT_USD (a probability-weighted
        blend of the sourced contained/catastrophic cost tiers above),
        against the cost of one proactive inspection instead.
      - An uncorroborated REVIEW (one signal only) is treated as a
        precautionary check, costed separately and NOT counted as an
        avoided failure -- because without corroboration we have no basis
        to claim it was a real defect; see backend/warrants.py for why
        corroboration gates escalation in the first place.
    """
    urgent = [w for w in warrants if w.severity_tier == "URGENT REVIEW" and w.corroborated]
    review_only = [w for w in warrants if w.severity_tier == "REVIEW"]

    n_avoided = len(urgent)
    cost_avoided = n_avoided * EXPECTED_COST_PER_MISSED_DEFECT_USD
    inspection_cost = n_avoided * COST_PROACTIVE_INSPECTION_USD + len(review_only) * COST_UNCORROBORATED_FALSE_ALARM_USD
    net_benefit = cost_avoided - inspection_cost

    fleet_size = max(len(set(w.asset_id for w in warrants)), 1)
    mttd_improvement_pct = (
        100.0 * (LEGACY_MEAN_TIME_TO_DETECT_HOURS - AXIOM_MEAN_TIME_TO_DETECT_HOURS)
        / LEGACY_MEAN_TIME_TO_DETECT_HOURS
    )

    return ROISummary(
        fleet_size=fleet_size,
        mission_ready_pct=0.0,  # filled in by caller with true fleet context
        urgent_review_count=len(urgent),
        review_count=len(review_only),
        estimated_failures_avoided=n_avoided,
        expected_cost_per_missed_defect_usd=EXPECTED_COST_PER_MISSED_DEFECT_USD,
        estimated_cost_avoided_usd=float(cost_avoided),
        estimated_inspection_cost_usd=float(inspection_cost),
        net_estimated_benefit_usd=float(net_benefit),
        legacy_mttd_hours=LEGACY_MEAN_TIME_TO_DETECT_HOURS,
        axiom_mttd_hours=AXIOM_MEAN_TIME_TO_DETECT_HOURS,
        mttd_improvement_pct=mttd_improvement_pct,
        contained_cost_range_usd=(CONTAINED_FAILURE_COST_LOW_USD, CONTAINED_FAILURE_COST_HIGH_USD),
        catastrophic_cost_usd=CATASTROPHIC_FAILURE_COST_USD,
        catastrophic_probability_assumption=P_CATASTROPHIC_GIVEN_MISSED_DEFECT,
        sourced_note=(
            "Contained-failure range ($5.0M-$13.5M) and catastrophic cost ($1.0B) are real, "
            "cited bearing-failure-related derailment costs (NTSB; DOJ/EPA on the Feb 3, 2023 "
            "East Palestine, OH derailment). See backend/roi.py docstring for full citations."
        ),
        assumptions_note=(
            f"The {P_CATASTROPHIC_GIVEN_MISSED_DEFECT:.0%} catastrophic-outcome probability, "
            "inspection costs, and detection-time figures are modeling ASSUMPTIONS, not published "
            "statistics -- no public base rate exists for how often a missed bearing defect goes "
            "catastrophic. Replace these with your own risk/cost data in backend/roi.py."
        ),
    )
