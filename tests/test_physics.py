import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from backend import physics as p


def test_kinetic_energy():
    assert p.kinetic_energy_j(1000, 10) == 50000.0
    assert p.kinetic_energy_j(0, 100) == 0.0


def test_coasting_flat_grade_decelerates_to_stop():
    r = p.coasting_profile(mass_kg=80000, velocity0_mps=20, grade_percent=0.0)
    assert r.will_accelerate_on_grade is False
    assert r.stop_distance_m is not None
    assert r.stop_time_s is not None
    assert r.velocities_mps[-1] == 0.0


def test_coasting_climbing_stops_sooner_than_flat():
    flat = p.coasting_profile(mass_kg=80000, velocity0_mps=20, grade_percent=0.0)
    climb = p.coasting_profile(mass_kg=80000, velocity0_mps=20, grade_percent=1.0)
    assert climb.stop_distance_m < flat.stop_distance_m


def test_coasting_steep_downgrade_accelerates():
    r = p.coasting_profile(mass_kg=80000, velocity0_mps=5, grade_percent=-3.0, max_time_s=600)
    assert r.will_accelerate_on_grade is True
    assert r.velocities_mps[-1] > r.velocities_mps[0]


def test_bearing_defect_frequency_ordering():
    # For a typical geometry (contact angle 0, d/D < 1), BPFO < shaft*n/2 < BPFI,
    # and FTF < shaft_hz (cage always turns slower than the shaft).
    freqs = p.bearing_defect_frequencies(shaft_hz=10, n_balls=8, ball_diameter_mm=15, pitch_diameter_mm=70)
    assert freqs["BPFO"] < 10 * 8 / 2 < freqs["BPFI"]
    assert freqs["FTF"] < 10


def test_bearing_defect_frequencies_sum_bpfo_bpfi_equals_n_times_shaft():
    # Textbook identity: BPFO + BPFI = n * f_r
    freqs = p.bearing_defect_frequencies(shaft_hz=12.3, n_balls=11, ball_diameter_mm=20, pitch_diameter_mm=90, contact_angle_deg=10)
    assert math.isclose(freqs["BPFO"] + freqs["BPFI"], 11 * 12.3, rel_tol=1e-9)


def test_fft_recovers_injected_frequency():
    fs = 1000.0
    t = np.arange(0, 2, 1 / fs)
    rng = np.random.default_rng(0)
    sig = 0.1 * rng.standard_normal(len(t)) + 1.0 * np.sin(2 * np.pi * 50 * t)
    freqs, mag = p.fft_spectrum(sig, fs)
    peak = p.detect_defect_peak(freqs, mag, target_hz=50, label="test")
    assert peak.found is True
    assert abs(peak.peak_hz - 50) < 1.0


def test_fft_does_not_falsely_detect_absent_frequency():
    fs = 1000.0
    t = np.arange(0, 2, 1 / fs)
    rng = np.random.default_rng(1)
    sig = 0.1 * rng.standard_normal(len(t))  # pure noise, no injected tone
    freqs, mag = p.fft_spectrum(sig, fs)
    peak = p.detect_defect_peak(freqs, mag, target_hz=50, label="test")
    assert peak.found is False


def test_zscore_sweep_flags_fault_well_below_fixed_threshold():
    """
    The core product claim: a rapid rate-of-change gets flagged even when
    absolute temperature stays under the legacy 170F fixed alarm.
    """
    times = np.arange(0, 3600, 10.0)
    n = len(times)
    rng = np.random.default_rng(2)
    normal = 120 + rng.standard_normal(n) * 0.2
    fault = normal.copy()
    start = n // 2
    fault[start:] += np.linspace(0, 35, n - start)  # rapid ramp, stays under 170F
    assert fault.max() < 170.0

    _, _, normal_alerts = p.zscore_sweep(normal, times)
    _, _, fault_alerts = p.zscore_sweep(fault, times)

    assert len(fault_alerts) > len(normal_alerts)
    assert any(a.severity in ("warning", "critical") for a in fault_alerts)


def test_ambient_relative_alarm_matches_east_palestine_record():
    """
    NTSB testimony on the Feb 3, 2023 East Palestine, OH derailment: the
    bearing read 253F above an ambient of 10F at the final detector before
    critical alarm. A fixed *absolute* threshold would not reflect how
    these systems are actually calibrated -- it is temperature ABOVE
    AMBIENT that matters.
    """
    r = p.ambient_relative_alarm(temp_f=10 + 253, ambient_f=10)
    assert r["delta_f"] == 253
    assert r["legacy_status"] == "critical"


def test_ambient_relative_alarm_hot_day_not_falsely_critical():
    # A bearing running at a normal 40F rise above a 95F summer ambient
    # should NOT trip critical, even though its absolute temperature
    # (135F) looks alarming out of context.
    r = p.ambient_relative_alarm(temp_f=95 + 40, ambient_f=95)
    assert r["legacy_status"] == "normal"


def test_robust_mad_zscore_flags_outlier_against_peers():
    rng = np.random.default_rng(0)
    peers = rng.normal(120, 2, 20)
    normal_reading = p.robust_mad_zscore(121, peers)
    fault_reading = p.robust_mad_zscore(150, peers)
    assert normal_reading.severity == "normal"
    assert fault_reading.severity == "critical"


def test_robust_mad_zscore_resists_outlier_contamination():
    # One wildly contaminated peer reading should barely move the
    # median/MAD-based score, unlike a mean/std z-score which it would
    # blow out completely.
    rng = np.random.default_rng(0)
    peers = rng.normal(120, 2, 20)
    clean = p.robust_mad_zscore(150, peers).robust_z
    contaminated = p.robust_mad_zscore(150, np.append(peers, 400)).robust_z
    assert abs(clean - contaminated) < 2.0


def test_zscore_sweep_quiet_on_flat_signal():
    times = np.arange(0, 3600, 10.0)
    n = len(times)
    rng = np.random.default_rng(3)
    flat = 100 + rng.standard_normal(n) * 0.1
    _, _, alerts = p.zscore_sweep(flat, times)
    assert len(alerts) == 0


def test_roi_mttd_matches_a1_workbook():
    """
    The dashboard's detection-time figures must match A1 sheet 2 row 5 (4.8 h
    legacy, 1.5 h AxiomDynamics). An earlier version of roi.py used 0.57 h and
    therefore advertised a 88% improvement where the workbook supports 69% --
    the same class of defect as the 29x cost overstatement: a number that looked
    better than the instrument that was supposed to produce it.
    """
    from backend import roi

    assert roi.LEGACY_MEAN_TIME_TO_DETECT_HOURS == 4.8, "A1 sheet 2 row 5"
    assert roi.AXIOM_MEAN_TIME_TO_DETECT_HOURS == 1.5, "A1 sheet 2 row 5"
    improvement = 100 * (1 - 1.5 / 4.8)
    assert roi.AXIOM_MEAN_TIME_TO_DETECT_HOURS < roi.LEGACY_MEAN_TIME_TO_DETECT_HOURS
    assert 68.0 < improvement < 69.5, "1.5 h against 4.8 h is 68.75%, not 88%"


def test_roi_expected_cost_matches_a1_workbook():
    """
    backend/roi.py's expected cost per missed defect must equal the A1
    workbook's B22 to the dollar: (1 - 0.0005) * 500,000 + 0.0005 * 1e9.

    This asserts the VALUE, not a formula rebuilt from the same constants.
    An earlier version of this test reconstructed `expected` from
    roi.P_CATASTROPHIC_GIVEN_MISSED_DEFECT and roi.TYPICAL_DERAILMENT_COST_USD
    and compared it to roi.EXPECTED_COST_PER_MISSED_DEFECT_USD -- which is a
    tautology: it passes whatever those constants are. Setting the probability
    back to 2% restored the 29x overstatement and the suite still reported 112
    passed, 0 failed. The literals below are the guard.
    """
    from backend import roi

    # A1 sheet 1: B17 = 0.05%, B14 = $500,000, B18 = $1,000,000,000.
    assert roi.P_CATASTROPHIC_GIVEN_MISSED_DEFECT == 0.0005, \
        "A1 B17 is 0.05%; a different value puts the dashboard out of step with the workbook"
    assert roi.TYPICAL_DERAILMENT_COST_USD == 500_000, "A1 B14 is $500,000"
    assert roi.CATASTROPHIC_FAILURE_COST_USD == 1_000_000_000, "A1 B18 is $1.0B"
    assert roi.EXPECTED_COST_PER_MISSED_DEFECT_USD == 999_750.0, \
        "A1 B22 is $999,750; anything else is the 29x defect returning"

    # The severe benchmarks are reference data and must not be mistaken for typical.
    assert roi.SEVERE_FAILURE_COST_LOW_USD == 5_000_000
    assert roi.SEVERE_FAILURE_COST_HIGH_USD == 13_500_000
    assert roi.TYPICAL_DERAILMENT_COST_USD < roi.SEVERE_FAILURE_COST_LOW_USD
    # And the expected value must sit below the severe pair: blending a severe
    # benchmark in as a typical is what produced $29,065,000.
    assert roi.EXPECTED_COST_PER_MISSED_DEFECT_USD < roi.SEVERE_FAILURE_COST_LOW_USD
    assert roi.EXPECTED_COST_PER_MISSED_DEFECT_USD < roi.CATASTROPHIC_FAILURE_COST_USD


def test_same_axle_differential_normal_when_close():
    r = p.same_axle_differential_alarm(100.0, 92.0)
    assert r["diff_f"] == 8.0
    assert r["status"] == "normal"


def test_same_axle_differential_critical_when_one_sided():
    r = p.same_axle_differential_alarm(214.2, 92.1)
    assert math.isclose(r["diff_f"], 122.1, rel_tol=1e-9)
    assert r["status"] == "critical"


def test_warrant_single_signal_capped_at_review():
    """
    Core safety rule from backend/warrants.py: a single flagged signal,
    even a critical one (e.g. an acoustic defect alone), must NOT escalate
    to URGENT REVIEW on its own -- it requires a second, independent
    signal to corroborate it first.
    """
    from backend.warrants import SignalEvidence, build_warrant, TIER_REVIEW

    evidence = [
        SignalEvidence("thermal_rate_of_change", "normal", "stable"),
        SignalEvidence("ambient_relative_legacy", "normal", "within range"),
        SignalEvidence("peer_historical", "normal", "within range"),
        SignalEvidence("peer_cross_fleet", "normal", "within range"),
        SignalEvidence("acoustic_bearing_defect", "critical", "BPFO peak, 100 sigma"),
    ]
    w = build_warrant(0, "TEST1", "TEST 001", "MP1", "Axle 1", 0.0, evidence)
    assert w is not None
    assert w.severity_tier == TIER_REVIEW
    assert w.corroborated is False


def test_warrant_two_signals_escalate_to_urgent_review():
    from backend.warrants import SignalEvidence, build_warrant, TIER_URGENT_REVIEW

    evidence = [
        SignalEvidence("thermal_rate_of_change", "critical", "rapid heating"),
        SignalEvidence("ambient_relative_legacy", "normal", "within range"),
        SignalEvidence("peer_historical", "critical", "far outside peer history"),
        SignalEvidence("peer_cross_fleet", "normal", "within range"),
        SignalEvidence("acoustic_bearing_defect", "normal", "no defect"),
    ]
    w = build_warrant(0, "TEST2", "TEST 002", "MP1", "Axle 1", 0.0, evidence)
    assert w is not None
    assert w.severity_tier == TIER_URGENT_REVIEW
    assert w.corroborated is True


def test_warrant_all_normal_produces_no_warrant():
    from backend.warrants import SignalEvidence, build_warrant

    evidence = [SignalEvidence(t, "normal", "ok") for t in
                ["thermal_rate_of_change", "ambient_relative_legacy", "peer_historical",
                 "peer_cross_fleet", "acoustic_bearing_defect"]]
    w = build_warrant(0, "TEST3", "TEST 003", "MP1", "Axle 1", 0.0, evidence)
    assert w is None


def test_warrant_hash_is_stable_and_sensitive_to_evidence():
    from backend.warrants import SignalEvidence, build_warrant

    evidence_a = [SignalEvidence("thermal_rate_of_change", "critical", "rapid heating")]
    evidence_b = [SignalEvidence("thermal_rate_of_change", "critical", "a different detail string")]
    w1 = build_warrant(0, "TEST4", "TEST 004", "MP1", "Axle 1", 0.0, evidence_a)
    w2 = build_warrant(0, "TEST4", "TEST 004", "MP1", "Axle 1", 0.0, evidence_a)
    w3 = build_warrant(0, "TEST4", "TEST 004", "MP1", "Axle 1", 0.0, evidence_b)
    assert w1.cryptographic_hash == w2.cryptographic_hash  # same inputs -> same hash
    assert w1.cryptographic_hash != w3.cryptographic_hash  # different evidence -> different hash


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
