"""
Synthetic fleet data generator.

There is no freely-downloadable, public, real-time locomotive/railcar
wayside sensor dataset (the datasets that exist, e.g. CWRU's bearing
vibration set, are generic motor-test-rig data behind a university host,
not rail axle data, and this sandbox has no outbound internet access to
fetch them anyway). So instead of faking "real" data, this module generates
synthetic sensor traces from the *same* physics equations in physics.py,
with known, documented fault conditions injected. That means every number
the dashboard shows can be traced back to an equation and a parameter you
can see right here -- nothing is hand-drawn.

Swapping this for a real wayside feed later means replacing the three
`generate_*` functions below with real data loaders that return the same
shapes; everything in main.py and physics.py is agnostic to where the
samples came from.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from . import physics

# ---------------------------------------------------------------------------
# Shared representative constants (order-of-magnitude realistic for a
# freight car tapered-roller journal bearing; NOT a specific OEM spec)
# ---------------------------------------------------------------------------
WHEEL_DIAMETER_M = 0.91          # 36 in wheel, common interchange size
BEARING_PITCH_DIAMETER_MM = 180.0
BEARING_BALL_DIAMETER_MM = 30.0
BEARING_N_ROLLERS = 15
BEARING_CONTACT_ANGLE_DEG = 12.0
BEARING_RACE_RADIUS_M = (BEARING_PITCH_DIAMETER_MM / 2.0) / 1000.0

THERMAL_MASS_KG = 50.0     # lumped bearing+housing thermal mass
STEEL_SPECIFIC_HEAT = 460.0  # J/(kg*K)
HEAT_TRANSFER_COEFF_W_PER_K = 27.0
RADIAL_LOAD_N = 50000.0    # representative loaded-car axle journal load

MU_NORMAL = 0.0018


@dataclass
class FleetUnit:
    unit_id: str
    reporting_mark_car: str
    axle_position: int
    mass_kg: float
    speed_mps: float
    scenario: str  # "normal" | "thermal_fault" | "acoustic_fault" | "both"
    upcoming_grade_percent: float
    fault_severity: float = 0.0  # 0..1, used to scale injected fault magnitude
    ambient_temp_f: float = 78.0  # varies per unit/route -- see note on East Palestine (10F that night)

    def bearing_geometry(self) -> Dict[str, float]:
        return {
            "n_balls": BEARING_N_ROLLERS,
            "ball_diameter_mm": BEARING_BALL_DIAMETER_MM,
            "pitch_diameter_mm": BEARING_PITCH_DIAMETER_MM,
            "contact_angle_deg": BEARING_CONTACT_ANGLE_DEG,
        }

    def shaft_hz(self) -> float:
        return physics.axle_shaft_hz(self.speed_mps, WHEEL_DIAMETER_M)


def build_fleet() -> List[FleetUnit]:
    """
    A representative 8-axle snapshot across 4 railcars, mixing normal axles
    with three distinct injected-fault axles so the dashboard has something
    to tell apart: a slow thermal bearing fault, an acoustic (outer-race
    spall) fault, and one axle running both at once (the worst case).
    """
    return [
        FleetUnit("U1", "BNSF 110234", 2, mass_kg=71_000, speed_mps=19.5,
                  scenario="normal", upcoming_grade_percent=0.4, ambient_temp_f=78.0),
        FleetUnit("U2", "BNSF 110234", 4, mass_kg=71_000, speed_mps=19.5,
                  scenario="normal", upcoming_grade_percent=0.4, ambient_temp_f=78.0),
        # U3: cold-night scenario, deliberately mirroring the East Palestine, OH
        # conditions (ambient ~10F) -- the point being that a slow thermal fault
        # here produces a modest ABSOLUTE temperature that would look unremarkable
        # out of context, while the rate-of-change and peer-group comparisons
        # still catch it.
        FleetUnit("U3", "BNSF 220881", 1, mass_kg=68_500, speed_mps=20.1,
                  scenario="thermal_fault", upcoming_grade_percent=-1.6, fault_severity=0.75,
                  ambient_temp_f=10.0),
        FleetUnit("U4", "BNSF 220881", 3, mass_kg=68_500, speed_mps=20.1,
                  scenario="normal", upcoming_grade_percent=-1.6, ambient_temp_f=10.0),
        FleetUnit("U5", "CSXT 551207", 2, mass_kg=64_900, speed_mps=17.8,
                  scenario="acoustic_fault", upcoming_grade_percent=0.9, fault_severity=0.8,
                  ambient_temp_f=92.0),
        FleetUnit("U6", "CSXT 551207", 4, mass_kg=64_900, speed_mps=17.8,
                  scenario="normal", upcoming_grade_percent=0.9, ambient_temp_f=92.0),
        FleetUnit("U7", "UP 883410", 1, mass_kg=73_200, speed_mps=21.0,
                  scenario="both", upcoming_grade_percent=-2.4, fault_severity=0.55,
                  ambient_temp_f=65.0),
        FleetUnit("U8", "UP 883410", 3, mass_kg=73_200, speed_mps=21.0,
                  scenario="normal", upcoming_grade_percent=-2.4, ambient_temp_f=65.0),
    ]


_FLEET_CACHE: Optional[List[FleetUnit]] = None


def get_fleet() -> List[FleetUnit]:
    global _FLEET_CACHE
    if _FLEET_CACHE is None:
        _FLEET_CACHE = build_fleet()
    return _FLEET_CACHE


def get_unit(unit_id: str) -> Optional[FleetUnit]:
    for u in get_fleet():
        if u.unit_id == unit_id:
            return u
    return None


# ---------------------------------------------------------------------------
# Thermodynamics: lumped bearing thermal model
#   dT/dt = (Q_friction - h*A*(T - T_ambient)) / (m * c_p)
#   Q_friction = mu(t) * F_radial * v_surface
# mu(t) is constant for a healthy bearing; for a faulted axle it ramps up
# partway through the window, modeling lubrication breakdown / incipient
# spalling increasing friction -- the physical mechanism a real rate-of-
# change detector is meant to catch before it crosses a fixed alarm point.
# ---------------------------------------------------------------------------

def _integrate_journal_temp(unit: FleetUnit, rng: np.random.Generator, duration_s: float, dt_s: float,
                             mu_max_scale: float, fault: bool) -> np.ndarray:
    """One journal's temperature trace (lumped thermal model), shared by
    both the left and right journal integrations below -- the only thing
    that differs between them is the friction coefficient ramp (whether,
    and how much, THIS journal is faulted)."""
    n_steps = int(duration_s // dt_s) + 1
    times_s = np.arange(n_steps) * dt_s
    ambient_c = (unit.ambient_temp_f - 32.0) * 5.0 / 9.0
    v_surface = 2 * math.pi * BEARING_RACE_RADIUS_M * unit.shaft_hz()
    mu_fault_max = MU_NORMAL + mu_max_scale
    fault_start_s = duration_s * 0.5

    T = ambient_c + 3.0
    temps_c = np.empty(n_steps)
    for i, t in enumerate(times_s):
        if fault and t >= fault_start_s:
            frac = min(1.0, (t - fault_start_s) / (duration_s * 0.5))
            mu = MU_NORMAL + frac * (mu_fault_max - MU_NORMAL)
        else:
            mu = MU_NORMAL
        q = mu * RADIAL_LOAD_N * v_surface
        dT = (q - HEAT_TRANSFER_COEFF_W_PER_K * (T - ambient_c)) / (THERMAL_MASS_KG * STEEL_SPECIFIC_HEAT) * dt_s
        T += dT
        temps_c[i] = T

    noise = rng.normal(0, 0.05, size=n_steps)  # ~0.09F, representative of a clean RTD/thermocouple
    return times_s, (temps_c + noise) * 9.0 / 5.0 + 32.0


def generate_thermo_series(unit: FleetUnit, duration_s: float = 3600.0, dt_s: float = 10.0,
                            seed: Optional[int] = None, fault_override: Optional[bool] = None,
                            fault_severity_override: Optional[float] = None):
    """
    Left-journal temperature trace (the "primary" reading used by the
    rate-of-change and ambient/peer checks elsewhere in the app).

    `fault_override`/`fault_severity_override` let callers (like the
    peer-history generator below) render the SAME unit as if it were
    healthy, for building a clean peer population to compare a live
    reading against -- without that, a unit's own injected-fault history
    would contaminate its own peer baseline.
    """
    rng = np.random.default_rng(seed if seed is not None else hash(unit.unit_id) % (2**32))
    fault = (unit.scenario in ("thermal_fault", "both")) if fault_override is None else fault_override
    severity = unit.fault_severity if fault_severity_override is None else fault_severity_override
    # "both" gets a somewhat gentler thermal ramp than a pure thermal fault,
    # since in that scenario the acoustic defect is the dominant signal.
    mu_scale = (0.0072 if unit.scenario == "thermal_fault" else 0.0045) * severity / 0.75
    return _integrate_journal_temp(unit, rng, duration_s, dt_s, mu_scale, fault)


def generate_right_journal_series(unit: FleetUnit, duration_s: float = 3600.0, dt_s: float = 10.0,
                                   seed: Optional[int] = None):
    """
    Right-journal trace for the SAME axle -- for the same-axle left/right
    differential check (standard HBD practice: the two journals on one
    axle share load path and speed, so they should track closely; a large
    gap points at a defect specific to one side).

    A healthy axle's two journals differ only by small random asymmetry
    (unequal load sharing, minor lubrication variance). "thermal_fault"
    axles in this demo are modeled as a ONE-SIDED defect (left journal
    only) -- consistent with how a real spalled race affects just the
    bearing it's in -- so for those units the right side stays healthy and
    the differential is expected to be large, which is exactly what this
    check is supposed to catch.
    """
    rng = np.random.default_rng(seed if seed is not None else (hash(unit.unit_id + "right") % (2**32)))
    fault = False  # right journal is never the injected-fault side in this demo fleet
    return _integrate_journal_temp(unit, rng, duration_s, dt_s, mu_max_scale=0.0, fault=fault)


# ---------------------------------------------------------------------------
# Multi-pass detector history: a peer/historical population to compare a
# live reading against. Models N previous wayside detector passes for this
# axle (its own history) plus a same-moment snapshot across the rest of the
# fleet (cross-axle peers) -- exactly the two populations your reference
# architecture's thermal model calls for ("historical baseline", "peer-
# group baseline"). Each entry is just the peak bearing temp delta-above-
# ambient recorded at that pass, which is the quantity HBDs actually log.
# ---------------------------------------------------------------------------

def _jittered_healthy_pass(unit: FleetUnit, rng: np.random.Generator) -> float:
    """
    One simulated healthy detector pass for `unit`, with realistic
    pass-to-pass variability: speed (load factor, which changes friction
    heat), ambient temperature (weather / time of day), and a small random
    walk in baseline lubrication friction. Without this, every "healthy"
    pass through the same deterministic physics model would come out
    almost identical (differing only by ~0.1F sensor noise), which collapses
    a robust peer comparison's spread to near zero and makes any z-score
    computed against it meaningless. Real bearing temperature readings
    vary pass-to-pass by several degrees even with no fault present.
    """
    jittered = dataclasses.replace(
        unit,
        speed_mps=unit.speed_mps * float(rng.uniform(0.9, 1.1)),
        ambient_temp_f=unit.ambient_temp_f + float(rng.uniform(-6.0, 6.0)),
    )
    pass_seed = int(rng.integers(0, 2**31))
    mu_jitter = float(rng.uniform(0.85, 1.15))  # +-15% healthy lubrication variability
    _, temps_f = generate_thermo_series(
        jittered, seed=pass_seed, fault_override=False,
    )
    # mu_jitter approximated post-hoc as a multiplicative nudge on the
    # resulting delta, since generate_thermo_series doesn't expose mu
    # directly -- keeps this function self-contained.
    delta = (float(temps_f.max()) - jittered.ambient_temp_f) * mu_jitter
    return delta


def generate_detector_pass_history(unit: FleetUnit, n_passes: int = 20, seed: Optional[int] = None):
    """Healthy-axle detector-pass history for `unit`, used as its own
    historical baseline. Always generated fault-free, even if `unit` itself
    has an injected fault in the live pass -- a bearing's PAST passes
    before a fault developed are, by definition, healthy."""
    rng = np.random.default_rng(seed if seed is not None else (hash(unit.unit_id + "hist") % (2**32)))
    return np.array([_jittered_healthy_pass(unit, rng) for _ in range(n_passes)])


def generate_cross_fleet_peer_deltas(unit: FleetUnit, seed: Optional[int] = None, n_samples_per_peer: int = 3):
    """Peer population: several simulated healthy-pass readings from every
    OTHER axle in the fleet, as a healthy-axle comparison cohort
    (route/environmental cohort in miniature -- this demo fleet isn't large
    enough to split further by route). Multiple samples per peer (rather
    than one) so the population has enough points for a stable MAD."""
    rng = np.random.default_rng(seed if seed is not None else (hash(unit.unit_id + "crossfleet") % (2**32)))
    deltas = []
    for peer in get_fleet():
        if peer.unit_id == unit.unit_id:
            continue
        for _ in range(n_samples_per_peer):
            deltas.append(_jittered_healthy_pass(peer, rng))
    return np.array(deltas)


# ---------------------------------------------------------------------------
# Acoustics: vibration signal with an optional outer-race defect harmonic
# riding on broadband sensor/mechanical noise plus a small 1x running-speed
# component (normal, healthy bearings are never perfectly silent at shaft
# frequency -- that's expected and is *not* itself a fault indicator).
# ---------------------------------------------------------------------------

def generate_acoustic_signal(unit: FleetUnit, duration_s: float = 2.0, sample_rate_hz: float = 5000.0,
                              seed: Optional[int] = None):
    rng = np.random.default_rng(seed if seed is not None else (hash(unit.unit_id + "ac") % (2**32)))
    n = int(duration_s * sample_rate_hz)
    t = np.arange(n) / sample_rate_hz

    shaft_hz = unit.shaft_hz()
    defect_freqs = physics.bearing_defect_frequencies(shaft_hz, **unit.bearing_geometry())

    signal = rng.normal(0, 0.08, size=n)                       # broadband noise floor
    signal += 0.03 * np.sin(2 * np.pi * shaft_hz * t)          # benign 1x imbalance component

    fault = unit.scenario in ("acoustic_fault", "both")
    if fault:
        amp = 0.25 + 0.5 * unit.fault_severity  # growing with severity (defect size)
        bpfo = defect_freqs["BPFO"]
        signal += amp * np.sin(2 * np.pi * bpfo * t)
        signal += 0.4 * amp * np.sin(2 * np.pi * 2 * bpfo * t)  # 2nd harmonic, typical of spalls

    return t, signal, defect_freqs, shaft_hz
