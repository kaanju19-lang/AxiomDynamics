"""
AxiomDynamics demo server.

Deliberately built on nothing but the Python standard library's http.server
(plus numpy for the math) -- no FastAPI, no uvicorn, no pip install beyond
numpy. Run it with:

    python3 -m backend.main

and open http://127.0.0.1:8420/ in a browser. That's the whole deployment
story, which is the point: this is meant to demonstrate that a predictive-
maintenance edge box doesn't need a software supply chain to work, which
matters a lot to a railroad's IT/security team evaluating an air-gapped
deployment.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict
from urllib.parse import urlparse, parse_qs

import numpy as np

from . import physics, simulate, warrants as warrants_mod, roi as roi_mod, store
from .warrants import SignalEvidence, build_warrant

store.init_db()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
# PORT is Render's (and most PaaS providers') convention: the platform sets
# it and expects the app to bind to it. AXIOM_PORT is kept as a fallback
# name for local/Docker use. Defaults to 8420 if neither is set.
PORT = int(os.environ.get("PORT", os.environ.get("AXIOM_PORT", "8420")))
# Defaults to localhost-only for a plain `python3 -m backend.main` run on a
# laptop. Inside Docker or on Render, set AXIOM_HOST=0.0.0.0 (the Dockerfile
# and render.yaml both do this) so the published port is actually reachable
# from outside the container/instance.
HOST = os.environ.get("AXIOM_HOST", "127.0.0.1")


def _jsonable(obj):
    """Recursively convert numpy scalars/arrays and dataclasses into plain
    JSON-serializable Python types."""
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return [_jsonable(x) for x in obj.tolist()]
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _jsonable(getattr(obj, k)) for k in obj.__dataclass_fields__}
    return obj


# ---------------------------------------------------------------------------
# Signal computation -- every route and the warrant builder draw from this
# one function so the fleet table, the alerts feed, and the per-unit detail
# charts can never disagree with each other about what fired.
# ---------------------------------------------------------------------------

def _severity_rank(s):
    return {"watch": 1, "warning": 2, "critical": 3}.get(s, 0)


def compute_unit_signals(u):
    """
    Runs every physics model for one axle and returns everything needed to
    both render the detail charts and build a fused Ghost Warrant:
      - raw series/spectra (for charts)
      - a list of SignalEvidence (one per independent model), for fusion
    """
    times, temps_f = simulate.generate_thermo_series(u)
    rates, zscores, rate_alerts = physics.zscore_sweep(temps_f, times)
    peak_temp_f = float(temps_f.max())

    legacy = physics.ambient_relative_alarm(peak_temp_f, u.ambient_temp_f)

    historical_peers = simulate.generate_detector_pass_history(u)
    peer_hist_result = physics.robust_mad_zscore(peak_temp_f - u.ambient_temp_f, historical_peers)

    cross_fleet_peers = simulate.generate_cross_fleet_peer_deltas(u)
    peer_cross_result = physics.robust_mad_zscore(peak_temp_f - u.ambient_temp_f, cross_fleet_peers)

    _, temps_right_f = simulate.generate_right_journal_series(u)
    peak_right_f = float(temps_right_f.max())
    differential = physics.same_axle_differential_alarm(peak_temp_f, peak_right_f)

    t, sig, defect_freqs, shaft_hz = simulate.generate_acoustic_signal(u)
    freqs, mag = physics.fft_spectrum(sig, 5000.0)
    acoustic_hit = physics.detect_defect_peak(freqs, mag, defect_freqs["BPFO"], "BPFO")

    worst_rate_severity = max((a.severity for a in rate_alerts), key=_severity_rank, default="normal")

    evidence = [
        SignalEvidence(
            signal_type="thermal_rate_of_change",
            severity=worst_rate_severity,
            detail=(f"Math: ({rate_alerts[-1].rate_f_per_min:.2f} F/min - baseline mean) / baseline std = "
                     f"z={rate_alerts[-1].zscore:.1f}" if rate_alerts else "stable, no abnormal heating rate"),
        ),
        SignalEvidence(
            signal_type="ambient_relative_legacy",
            severity={"normal": "normal", "warning": "warning", "critical": "critical"}[legacy["legacy_status"]],
            detail=(f"Math: {legacy['temp_f']:.1f}F - {legacy['ambient_f']:.1f}F = {legacy['delta_f']:.1f}F "
                     f"above ambient (legacy point-in-time check, limit {legacy['critical_delta_f']:.0f}F)"),
        ),
        SignalEvidence(
            signal_type="same_axle_differential",
            severity="critical" if differential["status"] == "critical" else "normal",
            detail=(f"Math: |{differential['temp_left_f']:.1f}F - {differential['temp_right_f']:.1f}F| = "
                     f"{differential['diff_f']:.1f}F left/right differential (limit {differential['critical_diff_f']:.0f}F)"),
        ),
        SignalEvidence(
            signal_type="peer_historical",
            severity=peer_hist_result.severity,
            detail=(f"Math: ({peak_temp_f - u.ambient_temp_f:.1f}F - median {peer_hist_result.median_peer:.1f}F) / "
                     f"(1.4826 x MAD {peer_hist_result.mad_peer:.1f}F) = z={peer_hist_result.robust_z:.1f} "
                     f"vs this axle's own last {len(historical_peers)} passes"),
        ),
        SignalEvidence(
            signal_type="peer_cross_fleet",
            severity=peer_cross_result.severity,
            detail=(f"Math: ({peak_temp_f - u.ambient_temp_f:.1f}F - median {peer_cross_result.median_peer:.1f}F) / "
                     f"(1.4826 x MAD {peer_cross_result.mad_peer:.1f}F) = z={peer_cross_result.robust_z:.1f} "
                     f"vs {len(cross_fleet_peers)} peer axles this pass"),
        ),
        SignalEvidence(
            signal_type="acoustic_bearing_defect",
            severity="critical" if acoustic_hit.found else "normal",
            detail=(f"BPFO peak at {acoustic_hit.peak_hz:.1f}Hz, {acoustic_hit.sigma_above_noise:.1f} sigma above noise floor"
                    if acoustic_hit.found else "no defect frequency above noise floor"),
        ),
    ]

    return {
        "times": times, "temps_f": temps_f, "rates": rates, "zscores": zscores,
        "rate_alerts": rate_alerts, "legacy": legacy, "differential": differential,
        "temps_right_f": temps_right_f,
        "peer_hist_result": peer_hist_result, "peer_cross_result": peer_cross_result,
        "freqs": freqs, "mag": mag, "defect_freqs": defect_freqs, "shaft_hz": shaft_hz,
        "acoustic_hit": acoustic_hit, "peak_temp_f": peak_temp_f, "evidence": evidence,
    }


def _tier_rank(tier):
    return {warrants_mod.TIER_INFORMATIONAL: 0, warrants_mod.TIER_REVIEW: 1,
            warrants_mod.TIER_URGENT_REVIEW: 2}.get(tier, 0)


# ---------------------------------------------------------------------------
# Route handlers -- each takes the parsed query dict, returns a JSON-able obj
# ---------------------------------------------------------------------------

def route_fleet(_query):
    out = []
    for i, u in enumerate(simulate.get_fleet()):
        sig = compute_unit_signals(u)
        warrant = build_warrant(
            advisory_seq=i, asset_id=u.unit_id, train_consist=u.reporting_mark_car,
            detector_location="MP (simulated)", component_position=f"Axle {u.axle_position} - Left",
            timestamp_s=float(sig["times"][-1]), evidence=sig["evidence"],
        )
        out.append({
            "unit_id": u.unit_id,
            "car": u.reporting_mark_car,
            "axle": u.axle_position,
            "speed_mps": u.speed_mps,
            "mass_kg": u.mass_kg,
            "ambient_temp_f": u.ambient_temp_f,
            "peak_temp_f": sig["peak_temp_f"],
            "thermo_alert_count": len(sig["rate_alerts"]),
            "acoustic_fault_found": sig["acoustic_hit"].found,
            "severity_tier": warrant.severity_tier if warrant else warrants_mod.TIER_INFORMATIONAL,
            "corroborated": warrant.corroborated if warrant else False,
        })
    return out


def route_unit_thermo(unit_id, _query):
    u = simulate.get_unit(unit_id)
    if u is None:
        return None
    sig = compute_unit_signals(u)
    return {
        "unit_id": unit_id,
        "times_s": sig["times"],
        "temps_f": sig["temps_f"],
        "temps_right_f": sig["temps_right_f"],
        "rates_f_per_min": sig["rates"],
        "zscores": sig["zscores"],
        "alerts": sig["rate_alerts"],
        "ambient_temp_f": u.ambient_temp_f,
        "legacy": sig["legacy"],
        "differential": sig["differential"],
        "peer_historical": sig["peer_hist_result"],
        "peer_cross_fleet": sig["peer_cross_result"],
    }


def route_unit_kinematics(unit_id, _query):
    u = simulate.get_unit(unit_id)
    if u is None:
        return None
    result = physics.coasting_profile(
        mass_kg=u.mass_kg,
        velocity0_mps=u.speed_mps,
        grade_percent=u.upcoming_grade_percent,
    )
    return {
        "unit_id": unit_id,
        "mass_kg": u.mass_kg,
        "initial_speed_mps": u.speed_mps,
        "grade_percent": u.upcoming_grade_percent,
        "initial_kinetic_energy_j": physics.kinetic_energy_j(u.mass_kg, u.speed_mps),
        "profile": result,
    }


def route_unit_acoustics(unit_id, _query):
    u = simulate.get_unit(unit_id)
    if u is None:
        return None
    t, sig, defect_freqs, shaft_hz = simulate.generate_acoustic_signal(u)
    freqs, mag = physics.fft_spectrum(sig, 5000.0)
    keep = freqs <= 500.0  # defect frequencies of interest are all well under this
    freqs_small, mag_small = freqs[keep], mag[keep]
    peaks = {
        label: physics.detect_defect_peak(freqs, mag, hz, label)
        for label, hz in defect_freqs.items()
    }
    return {
        "unit_id": unit_id,
        "shaft_hz": shaft_hz,
        "defect_frequencies_hz": defect_freqs,
        "spectrum_freqs_hz": freqs_small,
        "spectrum_magnitude": mag_small,
        "peaks": peaks,
    }


# ---------------------------------------------------------------------------
# Human reviewer disposition -- append-only since 2026-11-09 (AD-3).
#
# A disposition is never overwritten: a second decision on the same advisory is
# appended as a new row carrying `supersedes_id`, and the earlier row keeps its
# own content and timestamp. SQLite triggers refuse UPDATE and DELETE outright,
# and every row is chained by SHA-256 to the one before it, so a row edited or
# removed outside the app is detectable via store.verify_chain().
#
# This is what makes "REVIEW" / "URGENT REVIEW" an actual workflow step a named,
# credentialed person acts on, rather than a status string nothing ever writes
# back to -- the core of the "human-in-the-loop, AI never dispatches" story, and
# the record F09 produces.
# ---------------------------------------------------------------------------
VALID_DISPOSITIONS = {
    "concur_dispatch": "Concurred — dispatch order issued",
    "escalate": "Escalated to engineering/leadership",
    "override_downgrade": "Reviewer override — downgraded on field experience",
    "reject_sensor": "Rejected — suspected sensor/hardware fault, S&C dispatched",
}


def _disposition_label(rec):
    """'Label — Name (CERT)' plus a superseded-count marker when there is one."""
    label = (
        f"{VALID_DISPOSITIONS.get(rec['disposition'], rec['disposition'])} "
        f"— {rec['reviewer_name']} ({rec['cert_id']})"
    )
    history = store.disposition_history(rec["advisory_id"])
    if len(history) > 1:
        label += f" · supersedes {len(history) - 1} earlier record{'s' if len(history) > 2 else ''}"
    return label, len(history)


def _apply_disposition(warrant):
    rec = store.get_disposition(warrant.advisory_id)
    if rec:
        warrant.reviewer_disposition, warrant.disposition_history_count = _disposition_label(rec)
    return warrant


def route_alerts(_query):
    """
    Returns Predictive Ghost Warrants, not raw per-signal alerts. Each
    warrant fuses every independent model's reading for one axle and is
    only escalated to URGENT REVIEW when at least two independent signal
    types corroborate each other -- see backend/warrants.py for why.
    """
    out = []
    for i, u in enumerate(simulate.get_fleet()):
        sig = compute_unit_signals(u)
        warrant = build_warrant(
            advisory_seq=i, asset_id=u.unit_id, train_consist=u.reporting_mark_car,
            detector_location="MP (simulated)", component_position=f"Axle {u.axle_position} - Left",
            timestamp_s=float(sig["times"][-1]), evidence=sig["evidence"],
        )
        if warrant is not None:
            out.append(_apply_disposition(warrant))
    out.sort(key=lambda w: _tier_rank(w.severity_tier), reverse=True)
    return out


def route_roi(_query):
    fleet = simulate.get_fleet()
    warrants_list = route_alerts(_query)
    summary = roi_mod.compute_roi_summary(warrants_list)
    flagged_assets = {w.asset_id for w in warrants_list}
    summary.fleet_size = len(fleet)
    summary.mission_ready_pct = 100.0 * (1 - len(flagged_assets) / max(len(fleet), 1))
    return summary


def route_post_disposition(advisory_id, body):
    reviewer_name = (body.get("reviewer_name") or "").strip()
    cert_id = (body.get("cert_id") or "").strip()
    disposition = body.get("disposition")
    note = (body.get("note") or "").strip()
    if not reviewer_name or not cert_id or disposition not in VALID_DISPOSITIONS:
        return {"error": "reviewer_name, cert_id, and a valid disposition are required"}, 400
    if len(note) > 500:
        return {"error": "note must be 500 characters or fewer"}, 400

    # Appends. An earlier decision on this advisory is superseded, not replaced.
    rec = store.save_disposition(advisory_id, reviewer_name, cert_id, disposition, note)
    return {
        "ok": True,
        "advisory_id": advisory_id,
        "disposition": disposition,
        "record_id": rec["id"],
        "supersedes_id": rec["supersedes_id"],
        "recorded_at": rec["recorded_at"],
        "record_hash": rec["record_hash"],
    }, 200


def route_get_disposition_history(advisory_id):
    """
    The full decision trail for one advisory, oldest first. This is the record
    F09 produces: every decision, who made it, when, and what it corrected.
    """
    history = store.disposition_history(advisory_id)
    if not history:
        return {"advisory_id": advisory_id, "history": [], "count": 0,
                "chain_ok": store.verify_chain()["ok"]}, 200

    return {
        "advisory_id": advisory_id,
        "count": len(history),
        "history": [
            {
                "record_id": r["id"],
                "reviewer_name": r["reviewer_name"],
                "cert_id": r["cert_id"],
                "disposition": r["disposition"],
                "disposition_label": VALID_DISPOSITIONS.get(r["disposition"], r["disposition"]),
                "note": r["note"],
                "recorded_at": r["recorded_at"],
                "supersedes_id": r["supersedes_id"],
                "record_hash": r["record_hash"],
            }
            for r in history
        ],
        "chain_ok": store.verify_chain()["ok"],
    }, 200


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------

STATIC_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep the console quiet; flip this on for debugging

    def _send_json(self, payload, status=200):
        body = json.dumps(_jsonable(payload)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, rel_path):
        if rel_path in ("", "/"):
            rel_path = "index.html"
        rel_path = rel_path.lstrip("/")
        full_path = os.path.normpath(os.path.join(FRONTEND_DIR, rel_path))
        if not full_path.startswith(FRONTEND_DIR) or not os.path.isfile(full_path):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(full_path)[1]
        mime = STATIC_MIME.get(ext, "application/octet-stream")
        with open(full_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        try:
            if path.startswith("/api/warrant/") and path.endswith("/disposition"):
                # ['', 'api', 'warrant', '<advisory_id>', 'disposition']
                parts = path.split("/")
                if len(parts) == 5 and parts[3]:
                    result, status = route_get_disposition_history(parts[3])
                    return self._send_json(result, status=status)
            if path.startswith("/api/ledger/verify"):
                return self._send_json(store.verify_chain())
            if path == "/api/fleet":
                return self._send_json(route_fleet(query))
            if path == "/api/alerts":
                return self._send_json(route_alerts(query))
            if path == "/api/roi":
                return self._send_json(route_roi(query))
            if path.startswith("/api/unit/"):
                parts = path.split("/")  # ['', 'api', 'unit', '<id>', '<kind>']
                if len(parts) == 5:
                    unit_id, kind = parts[3], parts[4]
                    fn = {
                        "thermo": route_unit_thermo,
                        "kinematics": route_unit_kinematics,
                        "acoustics": route_unit_acoustics,
                    }.get(kind)
                    if fn:
                        result = fn(unit_id, query)
                        if result is None:
                            return self._send_json({"error": f"unknown unit_id {unit_id}"}, status=404)
                        return self._send_json(result)
            if path.startswith("/api/"):
                return self._send_json({"error": "unknown route"}, status=404)
            return self._send_static(path)
        except Exception as exc:  # pragma: no cover - defensive, keeps server alive
            self._send_json({"error": str(exc)}, status=500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        parts = path.split("/")  # ['', 'api', 'warrant', '<advisory_id>', 'disposition']
        try:
            if len(parts) == 5 and parts[1] == "api" and parts[2] == "warrant" and parts[4] == "disposition":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b"{}"
                body = json.loads(raw.decode("utf-8") or "{}")
                result, status = route_post_disposition(parts[3], body)
                return self._send_json(result, status=status)
            return self._send_json({"error": "unknown route"}, status=404)
        except Exception as exc:  # pragma: no cover
            self._send_json({"error": str(exc)}, status=500)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"AxiomDynamics demo server running at http://{HOST}:{PORT}/ (open http://127.0.0.1:{PORT}/ in a browser)")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
