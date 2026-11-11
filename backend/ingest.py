"""
Detector ingest — the inbound path B02 §2 specifies and B01 §7 item 5 discloses
as missing.

The claim under test here is narrow and specific: **a detector payload either
passes a defined validation chain and is accepted for scoring, or it is refused
with a named reason, and nothing reaches the physics engine in between.** B02 §2
puts it as "malformed input fails closed": it does not produce a low-confidence
advisory, it produces no advisory and a log entry.

That distinction is the whole design. A system that emits a weak signal for a bad
reading teaches reviewers to ignore weak signals, and a reviewer who has learned
to ignore the platform is worse than no platform — because the disposition ledger
now records that they ignored it.

The chain is B02 §2's three gates, in that order, and the ordering is deliberate:

    1. SCHEMA       - does the payload parse against the declared schema?
    2. TIMESTAMP    - is a timestamp present and coherent?
    3. PLAUSIBILITY - is the reading physically possible?

Gate 1 must come first because gates 2 and 3 read fields that may not exist. Gate
2 comes before gate 3 because a reading cannot be "physically implausible" until
we know when it was taken — a 212 F journal is alarming at 70 mph and unremarkable
on a stationary car in August.

**What this module does NOT do, and the docket must not be read as claiming:**

- It does not define the real detector payload schema. What is here is a
  demonstration schema, versioned (`SCHEMA_VERSION`), built from the fields the
  physics engine actually consumes. B02 §2 is explicit that the real schema must
  be agreed with the Railroad before production; swapping it is a bounded change
  to `PAYLOAD_SCHEMA` and its gate, which is why the schema is data rather than
  code.
- It does not authenticate the sender. There is no credential on this endpoint.
  That is the same gap as B01 §7 item 1 (AD-2) and the reason the ingest endpoint
  must stay off any interface reachable by anything but the Railroad's own
  collector on a trusted segment. **An unauthenticated ingest route is a
  data-poisoning route** — that is stated here rather than discovered later.
- It does not make the demonstration numbers real. A railroad's payload landing
  here makes that payload's numbers real; nothing else in the demo changes.
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "axiom-detector-payload/v1"

# ---------------------------------------------------------------------------
# The demonstration schema
# ---------------------------------------------------------------------------
# Declared as data so the real schema can replace it without rewriting the gate.
# `type`, `required`, `min`/`max` (numeric bounds), `enum`, `unit`.
#
# The physical bounds are not arbitrary. They are the range outside which no
# railroad journal bearing reading is credible, and each carries the reasoning
# that produced it — because a plausibility gate nobody can justify is a gate
# that gets widened in the field by whoever is losing the argument with it.
PAYLOAD_SCHEMA: Dict[str, Dict[str, Any]] = {
    "schema_version": {"type": str, "required": True,
                       "enum": [SCHEMA_VERSION]},
    "detector_id": {"type": str, "required": True, "min_len": 1, "max_len": 64},
    "unit_id": {"type": str, "required": True, "min_len": 1, "max_len": 64},
    "axle_position": {"type": int, "required": True, "min": 1, "max": 400,
                      "note": "a consist has at most a few hundred axles; a value "
                              "outside 1..400 is a parsing fault, not a reading"},
    "timestamp_unix": {"type": (int, float), "required": True,
                       "note": "seconds since epoch, UTC. Gate 2 checks this"},
    "ambient_temp_f": {"type": (int, float), "required": True, "min": -80.0,
                       "max": 140.0,
                       "note": "surface-record lows approach -60 F; a steel deck in "
                               "direct sun can read far above air temperature. Outside "
                               "-80..140 F this is a sensor fault, not weather"},
    "journal_temp_f": {"type": (int, float), "required": True, "min": -80.0,
                       "max": 900.0,
                       "note": "a seized bearing can reach the point of rail damage "
                               "near 900 F (D12 §2 keeps this decision-support, not an "
                               "alarm). Above that the sensor or the payload is wrong. "
                               "This is the OUTER bound; the scoring bound is tighter"},
    "speed_mps": {"type": (int, float), "required": True, "min": 0.0, "max": 90.0,
                  "note": "90 m/s is ~200 mph, above any freight service. A negative "
                          "speed is direction, not magnitude — the sender must send "
                          "magnitude"},
    "load_tonnes": {"type": (int, float), "required": False, "min": 0.0,
                    "max": 40000.0},
}

# Fields the physics engine needs to score a thermal reading. Anything missing
# here cannot be scored even if the payload is otherwise valid — so it is a
# schema requirement, not a plausibility question.
PHYSICS_REQUIRED = ("unit_id", "axle_position", "timestamp_unix",
                    "ambient_temp_f", "journal_temp_f", "speed_mps")


# ---------------------------------------------------------------------------
# Outcomes — a closed set, because an open one becomes a free-text field
# ---------------------------------------------------------------------------
REJECTED_SCHEMA = "rejected_schema"
REJECTED_TIMESTAMP = "rejected_timestamp"
REJECTED_PLAUSIBILITY = "rejected_plausibility"
ACCEPTED = "accepted"
SUSPECT = "suspect"


@dataclass
class IngestResult:
    """The outcome of one payload. `reason` is empty only when accepted."""
    outcome: str
    reason: str = ""
    payload: Optional[Dict[str, Any]] = None
    recorded_at: Optional[str] = None

    @property
    def accepted_for_scoring(self) -> bool:
        return self.outcome == ACCEPTED

    @property
    def emitted_an_advisory(self) -> bool:
        """B02 §2: a refused payload emits no advisory. Ever. This mirrors that."""
        return self.outcome == ACCEPTED


# ---------------------------------------------------------------------------
# Gate 1 — schema
# ---------------------------------------------------------------------------
def _validate_schema(payload: Any) -> Tuple[List[str], Dict[str, Any]]:
    """Return (problems, normalised). Problems empty means the payload parsed."""
    problems: List[str] = []
    if not isinstance(payload, dict):
        return (["payload is not a JSON object"], {})

    schema = PAYLOAD_SCHEMA
    for name, spec in schema.items():
        present = name in payload
        if spec.get("required") and not present:
            problems.append("missing required field %r" % name)
            continue
        if not present:
            continue
        val = payload[name]
        want = spec["type"]
        # bool is an int subclass in Python; a payload sending `true` for
        # axle_position must not pass as 1. Check bool explicitly.
        if isinstance(val, bool) and bool not in (
                want if isinstance(want, tuple) else (want,)):
            problems.append("field %r is a boolean, expected %s" % (
                name, getattr(want, "__name__", str(want))))
            continue
        if not isinstance(val, want):
            problems.append("field %r has type %s, expected %s" % (
                name, type(val).__name__,
                "/".join(getattr(w, "__name__", str(w))
                         for w in (want if isinstance(want, tuple) else (want,)))))
            continue
        if "enum" in spec and val not in spec["enum"]:
            problems.append("field %r is %r, this build accepts %r" % (
                name, val, spec["enum"]))
        if "min_len" in spec and len(val) < spec["min_len"]:
            problems.append("field %r is empty" % name)
        if "max_len" in spec and len(val) > spec["max_len"]:
            problems.append("field %r exceeds %d characters" % (
                name, spec["max_len"]))
        # Numeric bounds. These were declared in PAYLOAD_SCHEMA and NOT
        # enforced until a test written against the declared bound failed —
        # a schema that documents a limit and does not apply it is worse than
        # one with no limit, because the comment reads as a control.
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if "min" in spec and val < spec["min"]:
                problems.append("field %r is %r, below the physical minimum %r"
                                % (name, val, spec["min"]))
            if "max" in spec and val > spec["max"]:
                problems.append("field %r is %r, above the physical maximum %r"
                                % (name, val, spec["max"]))
        # NaN and infinity are valid floats to Python and invalid readings.
        if isinstance(val, float) and not math.isfinite(val):
            problems.append("field %r is %r, which is not a number a sensor can "
                            "report" % (name, val))

    unknown = set(payload) - set(schema)
    # Unknown fields are REFUSED, not ignored, for the same reason an added
    # top-level bundle field is refused (bundle_no_extras): a field nobody
    # validated rides along and a reader assumes it was checked.
    for name in sorted(unknown):
        problems.append("unknown field %r — this schema does not define it, so "
                        "nothing has validated it" % name)

    return problems, dict(payload)


# ---------------------------------------------------------------------------
# Gate 2 — timestamp
# ---------------------------------------------------------------------------
def _validate_timestamp(payload: Dict[str, Any], now: Optional[float] = None
                        ) -> List[str]:
    """Present and coherent. Not "is it plausible weather" — that is gate 3."""
    problems: List[str] = []
    ts = payload.get("timestamp_unix")
    if ts is None:
        return ["timestamp_unix is absent"]

    try:
        tsf = float(ts)
    except (TypeError, ValueError):
        return ["timestamp_unix is not numeric"]

    if not math.isfinite(tsf):
        return ["timestamp_unix is not finite"]

    now = time.time() if now is None else now
    # A reading from the future is a clock fault, and a clock fault silently
    # corrupts every interval computed from it — rate-of-change most of all,
    # which is the model that catches a bearing heating up. Five minutes of
    # tolerance absorbs NTP skew; more than that is not skew.
    if tsf > now + 300:
        problems.append("timestamp_unix is %d s in the future — a detector clock "
                        "fault corrupts every interval computed from this reading"
                        % int(tsf - now))
    # A reading from before the epoch is a parsing fault.
    if tsf < 0:
        problems.append("timestamp_unix is before 1970 — not a real detector time")
    return problems


# ---------------------------------------------------------------------------
# Gate 3 — physical plausibility
# ---------------------------------------------------------------------------
def _validate_plausibility(payload: Dict[str, Any]) -> List[str]:
    """
    Is the reading physically possible? B02 §2 draws a line between REJECT and
    SUSPECT, and it is not a soft/hard line — it is a line between impossible
    and merely unusual:
      * impossible  -> REJECTED_PLAUSIBILITY, not scored, not retained for scoring
      * unusual     -> SUSPECT, retained, not scored
    The schema bounds already reject impossible values. This gate catches
    combinations that are individually in range but jointly impossible.
    """
    problems: List[str] = []
    amb = float(payload["ambient_temp_f"])
    jrnl = float(payload["journal_temp_f"])
    speed = float(payload["speed_mps"])

    # A journal cannot be far BELOW ambient while the car is moving: friction
    # only adds heat. Allowing a small margin for sensor calibration, more than
    # 20 F below ambient while rolling is a probe fault, not a cold bearing.
    if speed > 1.0 and jrnl < amb - 20.0:
        problems.append(
            "journal %.1f F is more than 20 F BELOW ambient %.1f F while moving "
            "at %.1f m/s — friction adds heat, so this is a probe fault"
            % (jrnl, amb, speed))

    # Ambient above journal while stationary is possible (car sitting in sun,
    # probe reading air not metal) and is therefore SUSPECT, not a rejection.
    return problems


def _suspect_reasons(payload: Dict[str, Any]) -> List[str]:
    """Readings that are possible but should not be scored without a human."""
    reasons: List[str] = []
    amb = float(payload["ambient_temp_f"])
    jrnl = float(payload["journal_temp_f"])
    speed = float(payload["speed_mps"])

    if jrnl > 250.0:
        # Possible, and it is exactly what the platform exists to surface — but
        # B02 §2's gate is about whether the READING is trustworthy, not whether
        # the condition is serious. A journal at 250 F after a long climb is a
        # real thermal signature; it is not evidence the sensor is broken.
        pass
    if speed == 0.0 and jrnl - amb > 150.0:
        reasons.append("stationary axle reading %.1f F against %.1f F ambient — "
                       "possible after a hot-box stop; retained, not auto-scored"
                       % (jrnl, amb))
    return reasons


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------
def ingest(payload: Any, now: Optional[float] = None) -> IngestResult:
    """
    Run B02 §2's chain in order and return the outcome.

    The order is not decorative. Gate 1 first because gates 2 and 3 dereference
    fields that may not exist; gate 2 before gate 3 because a reading cannot be
    implausible until we know when it was taken. Reordering these produces a
    traceback on a malformed payload instead of a named refusal, which is the
    failure mode this function exists to prevent.
    """
    problems, normalised = _validate_schema(payload)
    if problems:
        return IngestResult(REJECTED_SCHEMA, "; ".join(problems))

    problems = _validate_timestamp(normalised, now=now)
    if problems:
        return IngestResult(REJECTED_TIMESTAMP, "; ".join(problems))

    problems = _validate_plausibility(normalised)
    if problems:
        return IngestResult(REJECTED_PLAUSIBILITY, "; ".join(problems))

    suspect = _suspect_reasons(normalised)
    if suspect:
        return IngestResult(SUSPECT, "; ".join(suspect), payload=normalised)

    return IngestResult(ACCEPTED, "", payload=normalised)


# ---------------------------------------------------------------------------
# Persistence and the reject log
# ---------------------------------------------------------------------------
REJECT_LOG_DDL = """
CREATE TABLE IF NOT EXISTS ingest_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at  TEXT NOT NULL DEFAULT (datetime('now')),
    outcome      TEXT NOT NULL,
    reason       TEXT NOT NULL,
    detector_id  TEXT,
    unit_id      TEXT,
    payload_sha  TEXT NOT NULL,
    payload_raw  TEXT NOT NULL
);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_ingest_log(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(REJECT_LOG_DDL)


def record(db_path: str, result: IngestResult, raw_payload: Any) -> int:
    """
    Append the outcome to the ingest log. **Every outcome is recorded, including
    acceptance** — B02 §2 says a rejection is logged, and a log that only
    contains failures cannot answer "how much did we accept last week", which is
    the question that matters when someone asks whether the platform was fed.

    The raw payload is stored for a REJECT because that is what an operator needs
    to diagnose a misconfigured collector; it is stored hashed-only for an
    ACCEPT to avoid retaining a second copy of every reading.
    """
    import hashlib
    raw = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"),
                     default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    keep_raw = result.outcome != ACCEPTED
    detector = unit = None
    if isinstance(raw_payload, dict):
        detector = raw_payload.get("detector_id")
        unit = raw_payload.get("unit_id")
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO ingest_log (outcome, reason, detector_id, unit_id, "
            "payload_sha, payload_raw) VALUES (?,?,?,?,?,?)",
            (result.outcome, result.reason,
             detector if isinstance(detector, str) else None,
             unit if isinstance(unit, str) else None,
             digest, raw if keep_raw else ""))
        return int(cur.lastrowid)


def ingest_and_record(db_path: str, payload: Any,
                      now: Optional[float] = None) -> IngestResult:
    """The path the HTTP route uses: validate, then log the outcome."""
    init_ingest_log(db_path)
    result = ingest(payload, now=now)
    result.recorded_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record(db_path, result, payload)
    return result
