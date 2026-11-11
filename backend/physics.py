"""
AxiomDynamics physics engine.

Three independent, named-physical-law analysis modules. Each one is a
deliberate upgrade over a specific legacy practice in freight rail wayside
monitoring, and each is implemented as plain, auditable math (no black-box
model) so a railroad's own engineers can verify every number by hand.

1. thermodynamics  Rate-of-change anomaly detection on wheel-bearing
                    temperature. Legacy hot-box detectors alarm on a fixed
                    absolute threshold (e.g. 170F). That misses a bearing
                    that is heating rapidly but hasn't crossed the line yet.
                    Here we track dT/dt (Newton's-law-of-cooling-consistent)
                    and flag when the *rate* is a statistical outlier
                    (z-score) against that axle's own recent baseline.

2. kinematics       Coasting distance/energy prediction from first
                    principles: KE = 1/2 m v^2, plus grade (gravity) and
                    resistance (rolling + aerodynamic drag) work terms,
                    integrated numerically.

3. acoustics        FFT-based bearing defect detection using the standard
                    rolling-element bearing defect-frequency equations
                    (BPFO, BPFI, BSF, FTF) from vibration analysis, not a
                    generic "listen for weird noise" model.

None of this is mystical. Every function below names the textbook equation
it implements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import numpy as np

# ===========================================================================
# 1. THERMODYNAMICS: rate-of-change (z-score) bearing temperature alerting
# ===========================================================================


def rolling_rate_of_change(temps_f: np.ndarray, times_s: np.ndarray, window: int = 5) -> np.ndarray:
    """
    dT/dt in degrees F per minute, via backward finite difference over a
    trailing `window` of samples. First `window` samples are NaN (no history
    yet).
    """
    temps_f = np.asarray(temps_f, dtype=float)
    times_s = np.asarray(times_s, dtype=float)
    n = len(temps_f)
    rates = np.full(n, np.nan)
    for i in range(window, n):
        dt_s = times_s[i] - times_s[i - window]
        if dt_s <= 0:
            continue
        dtemp = temps_f[i] - temps_f[i - window]
        rates[i] = dtemp / (dt_s / 60.0)
    return rates


@dataclass
class ThermoAlert:
    index: int
    time_s: float
    temp_f: float
    rate_f_per_min: float
    zscore: float
    severity: str  # "watch" | "warning" | "critical"


def zscore_sweep(
    temps_f: np.ndarray,
    times_s: np.ndarray,
    window: int = 10,
    baseline_window: int = 36,
    z_watch: float = 2.5,
    z_warning: float = 3.5,
    z_critical: float = 5.0,
    min_rate_f_per_min: float = 0.4,
) -> Tuple[np.ndarray, np.ndarray, List[ThermoAlert]]:
    """
    Compute rolling rate-of-change, then a rolling z-score of that rate
    against its own trailing baseline (mean/std over `baseline_window`
    prior samples). Flags a point when the current rate is an outlier
    relative to *that axle's own recent behavior* -- this is what lets the
    same logic work on a cold Montana morning and a hot Arizona afternoon
    without separate hand-tuned thresholds.

    `min_rate_f_per_min` suppresses alerts on essentially-flat traces where
    the z-score is mathematically large but physically meaningless (e.g.
    std is near zero so any tiny wobble looks like infinity sigma).

    Returns (rates, zscores, alerts).
    """
    rates = rolling_rate_of_change(temps_f, times_s, window=window)
    n = len(rates)
    zscores = np.full(n, np.nan)
    alerts: List[ThermoAlert] = []

    for i in range(window + baseline_window, n):
        baseline = rates[i - baseline_window:i]
        baseline = baseline[~np.isnan(baseline)]
        if len(baseline) < max(5, baseline_window // 2):
            continue
        mu = float(np.mean(baseline))
        sigma = float(np.std(baseline))
        if sigma < 1e-6:
            sigma = 1e-6
        z = (rates[i] - mu) / sigma
        zscores[i] = z

        if rates[i] < min_rate_f_per_min:
            continue
        if z >= z_critical:
            severity = "critical"
        elif z >= z_warning:
            severity = "warning"
        elif z >= z_watch:
            severity = "watch"
        else:
            continue
        alerts.append(
            ThermoAlert(
                index=i,
                time_s=float(times_s[i]),
                temp_f=float(temps_f[i]),
                rate_f_per_min=float(rates[i]),
                zscore=float(z),
                severity=severity,
            )
        )
    return rates, zscores, alerts


def ambient_relative_alarm(
    temp_f: float,
    ambient_f: float,
    warning_delta_f: float = 115.0,
    critical_delta_f: float = 170.0,
) -> Dict[str, object]:
    """
    Legacy hot-bearing detector (HBD) logic, modeled as actually deployed:
    alarms are set on temperature ABOVE AMBIENT, not an absolute number.
    This matches the real-world mechanism in the NTSB account of the
    February 3, 2023 East Palestine, OH derailment -- the bearing that
    failed read 253F above an ambient of 10F at the final detector before
    critical alarm, i.e. the absolute temperature (~263F) is not the
    number the system was actually checking; the DELTA against that
    night's cold ambient is.

    This function exists specifically so the dashboard can show, side by
    side, what a legacy point-in-time absolute/delta check would have said
    versus what the z-score rate-of-change sweep (above) says from the
    same data -- the core of the product's argument.
    """
    delta_f = temp_f - ambient_f
    if delta_f >= critical_delta_f:
        legacy_status = "critical"
    elif delta_f >= warning_delta_f:
        legacy_status = "warning"
    else:
        legacy_status = "normal"
    return {
        "temp_f": temp_f,
        "ambient_f": ambient_f,
        "delta_f": delta_f,
        "critical_delta_f": critical_delta_f,
        "legacy_status": legacy_status,
    }


@dataclass
class PeerZScoreResult:
    index: int
    time_s: float
    value: float
    median_peer: float
    mad_peer: float
    robust_z: float
    severity: str  # "normal" | "watch" | "warning" | "critical"


def robust_mad_zscore(
    value: float,
    peer_population: np.ndarray,
    z_watch: float = 2.5,
    z_warning: float = 3.5,
    z_critical: float = 5.0,
) -> PeerZScoreResult:
    """
    Robust (outlier-resistant) z-score of a single reading against a peer
    population, using median and MAD (median absolute deviation) instead
    of mean/std:

        Z = (x - median(P)) / (1.4826 * MAD(P))

    The 1.4826 constant scales MAD to be a consistent estimator of the
    standard deviation under a normal distribution, so this Z is
    comparable to an ordinary z-score but isn't dragged around by one or
    two extreme peer readings the way mean/std would be.

    `peer_population` can be ANY comparable population -- this same axle's
    history across past detector passes, a fleet-wide cohort of the same
    bearing type, or a route/environmental cohort (same line, similar
    ambient conditions) -- the math doesn't care which; the caller decides
    what "peer" means for a given comparison.
    """
    peer_population = np.asarray(peer_population, dtype=float)
    peer_population = peer_population[~np.isnan(peer_population)]
    if len(peer_population) == 0:
        return PeerZScoreResult(0, 0.0, value, value, 0.0, 0.0, "normal")

    median_p = float(np.median(peer_population))
    mad_p = float(np.median(np.abs(peer_population - median_p)))
    scaled_mad = 1.4826 * mad_p
    if scaled_mad < 1e-6:
        scaled_mad = 1e-6
    z = (value - median_p) / scaled_mad

    az = abs(z)
    if az >= z_critical:
        severity = "critical"
    elif az >= z_warning:
        severity = "warning"
    elif az >= z_watch:
        severity = "watch"
    else:
        severity = "normal"

    return PeerZScoreResult(
        index=0, time_s=0.0, value=float(value),
        median_peer=median_p, mad_peer=mad_p, robust_z=float(z), severity=severity,
    )


def same_axle_differential_alarm(
    temp_left_f: float,
    temp_right_f: float,
    critical_diff_f: float = 95.0,
) -> Dict[str, object]:
    """
    Same-axle left/right journal temperature differential check, standard
    industry hot-bearing practice alongside the ambient-relative check
    above: the two journals on one axle should run close to each other,
    since they share the same axle, same speed, same load path. A large
    gap between them points at ONE side failing specifically (e.g. a
    spalled race on just that journal), independent of what the ambient-
    relative absolute check says -- a bearing could be running hot on both
    sides from heavy load/high ambient (not necessarily a defect) while
    still showing a small, healthy differential; conversely a modest
    absolute temperature with a large differential is a red flag.

    This is deliberately a DIFFERENT signal from ambient_relative_alarm
    and zscore_sweep -- it's checking symmetry, not absolute level or
    trend -- which is why it's tracked as its own independent piece of
    evidence in the fusion/corroboration layer (see warrants.py).
    """
    diff_f = abs(temp_left_f - temp_right_f)
    status = "critical" if diff_f >= critical_diff_f else "normal"
    return {
        "temp_left_f": temp_left_f,
        "temp_right_f": temp_right_f,
        "diff_f": diff_f,
        "critical_diff_f": critical_diff_f,
        "status": status,
    }


# ===========================================================================
# 2. KINEMATICS: coasting distance / energy from E_k = 1/2 m v^2
# ===========================================================================

G = 9.80665  # m/s^2, standard gravity


def kinetic_energy_j(mass_kg: float, velocity_mps: float) -> float:
    """E_k = 1/2 m v^2, in joules."""
    return 0.5 * mass_kg * velocity_mps**2


@dataclass
class CoastResult:
    times_s: List[float]
    velocities_mps: List[float]
    distances_m: List[float]
    kinetic_energy_j: List[float]
    stop_distance_m: Optional[float]
    stop_time_s: Optional[float]
    will_accelerate_on_grade: bool


def coasting_profile(
    mass_kg: float,
    velocity0_mps: float,
    grade_percent: float,
    rolling_resistance_coeff: float = 0.0020,
    drag_coeff_area_m2: float = 6.0,
    air_density_kgm3: float = 1.225,
    dt_s: float = 0.5,
    max_time_s: float = 1800.0,
) -> CoastResult:
    """
    Numerically integrates the equation of motion for a coasting (throttle
    off, no braking) train on a constant grade:

        m * dv/dt = F_grade - F_roll - F_drag

        F_grade = m * G * sin(theta)              (positive = downgrade helps)
        F_roll  = rolling_resistance_coeff * m * G  (Davis-equation style term)
        F_drag  = 0.5 * air_density * drag_coeff_area_m2 * v^2

    grade_percent follows railroad convention (feet of rise per 100 feet of
    track, e.g. 1.0 = a 1% grade). Positive = climbing, negative = descending.

    This answers the dispatcher-relevant question "if this train goes to
    idle right now, how far does it roll and does it need to brake, or will
    the grade make it accelerate instead" -- useful for both fuel strategy
    and for flagging a car that is coasting abnormally short/far versus its
    predicted profile (which can itself be an early mechanical signal, e.g.
    excess rolling resistance from a dragging brake shoe).
    """
    theta = math.atan(grade_percent / 100.0)
    # Signed so that a positive result ACCELERATES the train: climbing
    # (theta > 0) decelerates it (gravity pulls back), descending
    # (theta < 0) accelerates it (gravity pulls forward).
    a_grade_signed = -G * math.sin(theta)
    f_roll_per_kg = rolling_resistance_coeff * G  # always opposes motion

    v = velocity0_mps
    d = 0.0
    t = 0.0
    times, vels, dists, kes = [0.0], [v], [0.0], [kinetic_energy_j(mass_kg, v)]

    # At v=0, drag is zero, so this tells us whether gravity alone (on a
    # descending grade) already beats rolling resistance: if so the train
    # will speed up while coasting rather than need braking, converging on
    # a terminal velocity once drag grows enough to balance it.
    will_accelerate = a_grade_signed > f_roll_per_kg

    stop_distance_m = None
    stop_time_s = None

    while t < max_time_s:
        drag_per_kg = 0.5 * air_density_kgm3 * drag_coeff_area_m2 * v * v / mass_kg
        a = a_grade_signed - f_roll_per_kg - drag_per_kg
        v_new = v + a * dt_s
        if v_new <= 0 and not will_accelerate:
            # Linear interpolation to the exact stop instant within this step.
            frac = v / (v - v_new) if (v - v_new) != 0 else 1.0
            d += v * (frac * dt_s) + 0.5 * a * (frac * dt_s) ** 2
            t += frac * dt_s
            v = 0.0
            stop_distance_m = d
            stop_time_s = t
            times.append(t)
            vels.append(v)
            dists.append(d)
            kes.append(0.0)
            break

        d += v * dt_s + 0.5 * a * dt_s**2
        v = max(v_new, 0.0) if not will_accelerate else v_new
        t += dt_s
        times.append(t)
        vels.append(v)
        dists.append(d)
        kes.append(kinetic_energy_j(mass_kg, v))

        if will_accelerate and v > velocity0_mps * 3:
            # Safety cutoff: profile has clearly diverged (runaway on grade),
            # stop simulating further -- the point (needs intervention) is made.
            break

    return CoastResult(
        times_s=times,
        velocities_mps=vels,
        distances_m=dists,
        kinetic_energy_j=kes,
        stop_distance_m=stop_distance_m,
        stop_time_s=stop_time_s,
        will_accelerate_on_grade=will_accelerate,
    )


# ===========================================================================
# 3. ACOUSTICS: FFT bearing-defect detection
# ===========================================================================


def bearing_defect_frequencies(
    shaft_hz: float,
    n_balls: int,
    ball_diameter_mm: float,
    pitch_diameter_mm: float,
    contact_angle_deg: float = 0.0,
) -> Dict[str, float]:
    """
    Standard rolling-element bearing characteristic defect frequencies
    (Hz), as used throughout industrial vibration analysis (see e.g. SKF /
    Timken bearing diagnostics literature):

        BPFO = (n/2) * f_r * (1 - (d/D) cos(theta))   outer race defect
        BPFI = (n/2) * f_r * (1 + (d/D) cos(theta))   inner race defect
        BSF  = (D/2d) * f_r * (1 - (d/D)^2 cos^2(theta))  ball (rolling element) defect
        FTF  = (f_r/2) * (1 - (d/D) cos(theta))        cage (fundamental train) frequency

    where f_r is the shaft rotation frequency (Hz), n is the number of
    rolling elements, d is ball diameter, D is pitch diameter, theta is the
    contact angle.

    shaft_hz for a rail axle is derived from train speed and wheel diameter:
    f_r = v / (pi * wheel_diameter).
    """
    d_over_D = ball_diameter_mm / pitch_diameter_mm
    cos_t = math.cos(math.radians(contact_angle_deg))
    bpfo = (n_balls / 2.0) * shaft_hz * (1 - d_over_D * cos_t)
    bpfi = (n_balls / 2.0) * shaft_hz * (1 + d_over_D * cos_t)
    bsf = (pitch_diameter_mm / (2.0 * ball_diameter_mm)) * shaft_hz * (1 - (d_over_D * cos_t) ** 2)
    ftf = (shaft_hz / 2.0) * (1 - d_over_D * cos_t)
    return {"BPFO": bpfo, "BPFI": bpfi, "BSF": bsf, "FTF": ftf}


def axle_shaft_hz(speed_mps: float, wheel_diameter_m: float) -> float:
    """Shaft rotation frequency f_r = v / (pi * wheel_diameter)."""
    if wheel_diameter_m <= 0:
        return 0.0
    return speed_mps / (math.pi * wheel_diameter_m)


def fft_spectrum(signal: np.ndarray, sample_rate_hz: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    One-sided amplitude spectrum via real FFT. Returns (freqs_hz, magnitude).
    """
    signal = np.asarray(signal, dtype=float)
    n = len(signal)
    window = np.hanning(n)
    spectrum = np.fft.rfft(signal * window)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)
    magnitude = np.abs(spectrum) / n
    return freqs, magnitude


@dataclass
class DefectPeakResult:
    label: str
    target_hz: float
    found: bool
    peak_hz: Optional[float]
    peak_magnitude: Optional[float]
    noise_floor: float
    sigma_above_noise: float


def detect_defect_peak(
    freqs: np.ndarray,
    magnitude: np.ndarray,
    target_hz: float,
    label: str,
    tolerance_hz: float = 3.0,
    sigma_threshold: float = 4.0,
) -> DefectPeakResult:
    """
    Looks for a spectral peak within `tolerance_hz` of a theoretical defect
    frequency (BPFO/BPFI/BSF/FTF, or a harmonic of one) and checks whether
    it stands `sigma_threshold` standard deviations above the broadband
    noise floor (noise floor estimated from the whole spectrum excluding a
    guard band around the target). This is a standard "spectral kurtosis /
    peak prominence" style check, not a magnitude-only threshold -- a loud
    but broadband-noisy spectrum won't false-positive.
    """
    freqs = np.asarray(freqs)
    magnitude = np.asarray(magnitude)
    band = (freqs >= target_hz - tolerance_hz) & (freqs <= target_hz + tolerance_hz)
    guard = (freqs >= target_hz - 5 * tolerance_hz) & (freqs <= target_hz + 5 * tolerance_hz)

    if not np.any(band) or np.sum(~guard) < 10:
        return DefectPeakResult(label, target_hz, False, None, None, 0.0, 0.0)

    noise_pool = magnitude[~guard]
    noise_floor = float(np.mean(noise_pool))
    noise_sigma = float(np.std(noise_pool)) or 1e-9

    idx_in_band = np.where(band)[0]
    peak_idx = idx_in_band[np.argmax(magnitude[idx_in_band])]
    peak_mag = float(magnitude[peak_idx])
    peak_hz = float(freqs[peak_idx])
    sigma_above = (peak_mag - noise_floor) / noise_sigma

    found = sigma_above >= sigma_threshold
    return DefectPeakResult(
        label=label,
        target_hz=target_hz,
        found=found,
        peak_hz=peak_hz,
        peak_magnitude=peak_mag,
        noise_floor=noise_floor,
        sigma_above_noise=float(sigma_above),
    )
