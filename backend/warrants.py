"""
Predictive Ghost Warrant construction.

A "Ghost Warrant" is this product's name for a single traceable evidence
packet: one axle, one point in time, every signal that fired on it, a
severity tier, and a cryptographic hash binding the record so it can't be
quietly edited after the fact. This is the audit/evidence-trail layer that
turns "the dashboard said critical" into something a railroad's safety and
legal team can actually stand behind.

Two design choices worth calling out explicitly:

1. Severity tiers are named INFORMATIONAL / REVIEW / URGENT REVIEW, not
   "watch/warning/critical" -- the point of the rename is to make it
   impossible to mistake these for operational alarm levels. See the
   CRITICAL SAFETY GUARDRAIL note below and in the README: this system
   never issues a stop-train or braking instruction. It produces evidence
   for a human to review. Existing railroad operating rules, detector
   logic, and authorized personnel remain the sole authority over any
   train-movement decision.

2. Escalation to URGENT REVIEW requires CORROBORATION: at least two
   independent signal types (e.g. thermal rate-of-change AND a peer-group
   outlier, or thermal AND acoustic) must agree. A single signal, even one
   that is itself severe, is capped at REVIEW. This directly implements
   the infographic's "acoustic detection requires corroboration before
   fracture classification" rule, generalized across all signal types, so
   one noisy sensor can't single-handedly manufacture a false urgent case.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

# Internal physics-module severities ("watch"/"warning"/"critical") map
# onto a 0..3 ordinal so independent signals can be compared and combined.
_SEVERITY_ORDINAL = {None: 0, "normal": 0, "watch": 1, "warning": 2, "critical": 3}

TIER_INFORMATIONAL = "INFORMATIONAL"
TIER_REVIEW = "REVIEW"
TIER_URGENT_REVIEW = "URGENT REVIEW"

RECOMMENDED_RESPONSE = {
    TIER_INFORMATIONAL: "Record in audit ledger. No operational action required.",
    TIER_REVIEW: "Authorized analyst examination and prioritization.",
    TIER_URGENT_REVIEW: "Escalate to authorized railroad personnel per carrier-approved procedures.",
}


@dataclass
class SignalEvidence:
    """One independent signal's reading on this axle at this pass."""
    signal_type: str          # "thermal_rate_of_change" | "ambient_relative_legacy" | "peer_historical" | "peer_cross_fleet" | "acoustic_bearing_defect"
    severity: str             # "normal" | "watch" | "warning" | "critical"
    detail: str
    confidence_note: str = ""


@dataclass
class GhostWarrant:
    advisory_id: str
    asset_id: str
    train_consist: str
    detector_location: str
    component_position: str
    timestamp_s: float
    severity_tier: str
    corroborated: bool
    evidence: List[SignalEvidence]
    reference_population_version: str
    model_version: str
    confidence: str
    recommended_response: str
    reviewer_disposition: str
    ground_truth_status: str
    cryptographic_hash: str


REFERENCE_POPULATION_VERSION = "v1.4.2"   # stands in for a real versioned baseline dataset
MODEL_VERSION = "0.97"                     # stands in for a real model/ruleset version


def _severity_to_tier(worst_ordinal: int, corroborated: bool) -> str:
    if worst_ordinal <= 0:
        return TIER_INFORMATIONAL
    if worst_ordinal >= 3 and corroborated:
        return TIER_URGENT_REVIEW
    if worst_ordinal >= 2 and corroborated:
        return TIER_URGENT_REVIEW
    # Severe-but-uncorroborated, or merely moderate: held at REVIEW, not
    # escalated further, until a second independent signal agrees.
    return TIER_REVIEW


def build_warrant(
    advisory_seq: int,
    asset_id: str,
    train_consist: str,
    detector_location: str,
    component_position: str,
    timestamp_s: float,
    evidence: List[SignalEvidence],
    confidence: Optional[str] = None,
    reviewer_disposition: str = "Pending",
    ground_truth_status: str = "Not available",
) -> Optional[GhostWarrant]:
    """
    Fuses a set of independent signal readings for one axle/pass into a
    single Ghost Warrant. Returns None if every signal is normal (no
    warrant is generated for a clean reading -- nothing to review).
    """
    flagged = [e for e in evidence if _SEVERITY_ORDINAL.get(e.severity, 0) > 0]
    if not flagged:
        return None

    worst_ordinal = max(_SEVERITY_ORDINAL.get(e.severity, 0) for e in evidence)
    distinct_signal_types_flagged = {e.signal_type for e in flagged}
    corroborated = len(distinct_signal_types_flagged) >= 2

    tier = _severity_to_tier(worst_ordinal, corroborated)

    if confidence is None:
        confidence = "High" if corroborated else "Moderate (single signal, uncorroborated)"

    advisory_id = f"AD-{2025}-{advisory_seq:04d}"

    canonical = json.dumps({
        "advisory_id": advisory_id,
        "asset_id": asset_id,
        "timestamp_s": timestamp_s,
        "evidence": [asdict(e) for e in evidence],
        "model_version": MODEL_VERSION,
        "reference_population_version": REFERENCE_POPULATION_VERSION,
    }, sort_keys=True)
    crypto_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return GhostWarrant(
        advisory_id=advisory_id,
        asset_id=asset_id,
        train_consist=train_consist,
        detector_location=detector_location,
        component_position=component_position,
        timestamp_s=timestamp_s,
        severity_tier=tier,
        corroborated=corroborated,
        evidence=evidence,
        reference_population_version=REFERENCE_POPULATION_VERSION,
        model_version=MODEL_VERSION,
        confidence=confidence,
        recommended_response=RECOMMENDED_RESPONSE[tier],
        reviewer_disposition=reviewer_disposition,
        ground_truth_status=ground_truth_status,
        cryptographic_hash=crypto_hash,
    )
