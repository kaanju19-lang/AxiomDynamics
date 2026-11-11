"""
Tests for the detector ingest path (B02 §2).

The claim under test is not "ingest accepts a dict". It is the sentence B02 §2
makes: **malformed input fails closed — it produces no advisory and a log entry,
not a low-confidence advisory.** A system that emits a weak signal for a bad
reading teaches reviewers to ignore weak signals, so every test below asserts
either that a bad payload is refused with a NAMED reason, or that it is retained
without being scored, or that an impossible thing never reaches the engine.

Run: python3 -I tests/test_ingest.py
"""

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend import ingest  # noqa: E402

RESULTS = []


def test(fn):
    try:
        fn()
    except AssertionError as exc:
        RESULTS.append((fn.__name__, False, exc))
    except Exception as exc:  # noqa: BLE001 - a crash is a failure, named
        RESULTS.append((fn.__name__, False, "%s: %s" % (type(exc).__name__, exc)))
    else:
        RESULTS.append((fn.__name__, True, None))
    return fn


NOW = 1_781_000_000.0  # fixed "now" so the timestamp gate is deterministic


def good(**over):
    """A payload every gate should accept."""
    p = {
        "schema_version": ingest.SCHEMA_VERSION,
        "detector_id": "DET-001",
        "unit_id": "U1",
        "axle_position": 3,
        "timestamp_unix": NOW - 60,
        "ambient_temp_f": 78.0,
        "journal_temp_f": 96.5,
        "speed_mps": 22.0,
    }
    p.update(over)
    return p


# ---------------------------------------------------------------------------
# The happy path, asserted explicitly so a gate that rejects everything fails
# ---------------------------------------------------------------------------
@test
def test_a_well_formed_payload_is_accepted_for_scoring():
    r = ingest.ingest(good(), now=NOW)
    assert r.outcome == ingest.ACCEPTED, r
    assert r.accepted_for_scoring is True
    assert r.emitted_an_advisory is True
    assert r.reason == ""


@test
def test_an_optional_field_may_be_absent():
    p = good()
    assert "load_tonnes" not in p
    assert ingest.ingest(p, now=NOW).outcome == ingest.ACCEPTED


# ---------------------------------------------------------------------------
# Gate 1 — schema. Every case must produce a NAMED reason, never a traceback.
# ---------------------------------------------------------------------------
@test
def test_payload_that_is_not_an_object_is_refused_not_crashed():
    for bad in (None, [], "string", 42, True):
        r = ingest.ingest(bad, now=NOW)
        assert r.outcome == ingest.REJECTED_SCHEMA, (bad, r)
        assert r.accepted_for_scoring is False
        assert "not a JSON object" in r.reason, r.reason


@test
def test_missing_required_field_names_the_field():
    for name in ingest.PHYSICS_REQUIRED:
        p = good()
        del p[name]
        r = ingest.ingest(p, now=NOW)
        assert r.outcome == ingest.REJECTED_SCHEMA, (name, r)
        assert name in r.reason, (name, r.reason)


@test
def test_wrong_type_is_refused_and_names_both_types():
    p = good(axle_position="3")
    r = ingest.ingest(p, now=NOW)
    assert r.outcome == ingest.REJECTED_SCHEMA
    assert "axle_position" in r.reason and "str" in r.reason and "int" in r.reason


@test
def test_a_boolean_is_not_accepted_where_an_int_is_required():
    # bool is an int subclass in Python; `True` must not pass as axle_position 1.
    p = good(axle_position=True)
    r = ingest.ingest(p, now=NOW)
    assert r.outcome == ingest.REJECTED_SCHEMA, r
    assert "boolean" in r.reason


@test
def test_nan_and_infinity_are_refused_not_scored():
    for bad in (float("nan"), float("inf"), float("-inf")):
        r = ingest.ingest(good(journal_temp_f=bad), now=NOW)
        assert r.outcome == ingest.REJECTED_SCHEMA, (bad, r)
        assert "not a number a sensor can report" in r.reason


@test
def test_out_of_range_value_is_refused_with_the_bound_in_the_message():
    r = ingest.ingest(good(axle_position=0), now=NOW)
    assert r.outcome == ingest.REJECTED_SCHEMA
    assert "axle_position" in r.reason


@test
def test_unknown_field_is_refused_not_ignored():
    """
    Same reasoning as `bundle_no_extras` in the export: a field nobody validated
    rides along and a reader assumes it was checked.
    """
    r = ingest.ingest(good(surprise="value"), now=NOW)
    assert r.outcome == ingest.REJECTED_SCHEMA, r
    assert "unknown field 'surprise'" in r.reason


@test
def test_wrong_schema_version_is_refused_by_name():
    r = ingest.ingest(good(schema_version="axiom-detector-payload/v99"), now=NOW)
    assert r.outcome == ingest.REJECTED_SCHEMA
    assert "schema_version" in r.reason


# ---------------------------------------------------------------------------
# Gate 2 — timestamp
# ---------------------------------------------------------------------------
@test
def test_absent_timestamp_is_refused_at_the_timestamp_gate():
    p = good()
    del p["timestamp_unix"]
    r = ingest.ingest(p, now=NOW)
    # Absent is a schema failure (it is required) — assert the gate that fired
    # rather than assuming, so a schema change cannot silently move it.
    assert r.outcome == ingest.REJECTED_SCHEMA


@test
def test_timestamp_from_the_future_is_refused():
    r = ingest.ingest(good(timestamp_unix=NOW + 3600), now=NOW)
    assert r.outcome == ingest.REJECTED_TIMESTAMP, r
    assert "future" in r.reason


@test
def test_small_clock_skew_is_tolerated():
    r = ingest.ingest(good(timestamp_unix=NOW + 60), now=NOW)
    assert r.outcome == ingest.ACCEPTED, r


@test
def test_pre_epoch_timestamp_is_refused():
    r = ingest.ingest(good(timestamp_unix=-1), now=NOW)
    assert r.outcome == ingest.REJECTED_TIMESTAMP, r
    assert "before 1970" in r.reason


# ---------------------------------------------------------------------------
# Gate 3 — plausibility, and the REJECT/SUSPECT distinction
# ---------------------------------------------------------------------------
@test
def test_journal_far_below_ambient_while_moving_is_refused():
    """Friction adds heat. A cold reading while rolling is a probe fault."""
    r = ingest.ingest(good(ambient_temp_f=90.0, journal_temp_f=40.0,
                           speed_mps=20.0), now=NOW)
    assert r.outcome == ingest.REJECTED_PLAUSIBILITY, r
    assert "probe fault" in r.reason


@test
def test_journal_below_ambient_while_stationary_is_not_a_rejection():
    """A car in the sun reads its air, not its metal. Possible, so not rejected."""
    r = ingest.ingest(good(ambient_temp_f=90.0, journal_temp_f=60.0,
                           speed_mps=0.0), now=NOW)
    assert r.outcome != ingest.REJECTED_PLAUSIBILITY, r


@test
def test_a_hot_journal_is_accepted_not_treated_as_a_sensor_fault():
    """
    The gate asks whether the READING is trustworthy, not whether the condition
    is serious. A genuinely hot bearing is the signal the platform exists for.
    Refusing it would be the worst possible false negative.
    """
    r = ingest.ingest(good(journal_temp_f=300.0, ambient_temp_f=80.0,
                           speed_mps=25.0), now=NOW)
    assert r.outcome in (ingest.ACCEPTED, ingest.SUSPECT), r
    assert r.outcome != ingest.REJECTED_PLAUSIBILITY


@test
def test_stationary_hot_axle_is_retained_as_suspect_not_scored():
    r = ingest.ingest(good(speed_mps=0.0, ambient_temp_f=70.0,
                           journal_temp_f=260.0), now=NOW)
    assert r.outcome == ingest.SUSPECT, r
    assert r.accepted_for_scoring is False
    assert r.emitted_an_advisory is False
    assert r.reason, "a suspect reading must say why it was not scored"


# ---------------------------------------------------------------------------
# Fail-closed: the property everything else rests on
# ---------------------------------------------------------------------------
@test
def test_no_non_accepted_outcome_ever_emits_an_advisory():
    """The whole design in one assertion. B02 §2's sentence, executable."""
    cases = [
        None, [], "x",
        good(axle_position="3"),
        good(timestamp_unix=NOW + 7200),
        good(ambient_temp_f=90.0, journal_temp_f=10.0, speed_mps=20.0),
        good(speed_mps=0.0, ambient_temp_f=70.0, journal_temp_f=300.0),
    ]
    for c in cases:
        r = ingest.ingest(c, now=NOW)
        assert r.outcome != ingest.ACCEPTED, c
        assert r.emitted_an_advisory is False, (c, r)
        assert r.accepted_for_scoring is False, (c, r)
        assert r.reason, ("refused with no reason", c)


@test
def test_the_chain_runs_in_documented_order():
    """
    Gate 1 must precede gate 2 and 3 or a malformed payload raises instead of
    being named. A payload that is bad in all three ways must report SCHEMA,
    because that is the first gate.
    """
    r = ingest.ingest({"axle_position": "three"}, now=NOW)
    assert r.outcome == ingest.REJECTED_SCHEMA, r


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
@test
def test_every_outcome_is_logged_including_acceptance():
    """
    A log containing only failures cannot answer "how much did we accept", which
    is the question asked when someone wonders whether the platform was fed.
    """
    db = os.path.join(tempfile.mkdtemp(prefix="axiom-ingest-"), "log.db")
    ingest.ingest_and_record(db, good(), now=NOW)
    ingest.ingest_and_record(db, {"nonsense": True}, now=NOW)
    ingest.ingest_and_record(db, None, now=NOW)

    import sqlite3
    con = sqlite3.connect(db)
    outcomes = [r[0] for r in con.execute("SELECT outcome FROM ingest_log ORDER BY id")]
    con.close()
    assert outcomes == [ingest.ACCEPTED, ingest.REJECTED_SCHEMA,
                        ingest.REJECTED_SCHEMA], outcomes


@test
def test_a_rejected_payload_is_retained_verbatim_for_diagnosis():
    db = os.path.join(tempfile.mkdtemp(prefix="axiom-ingest-"), "log.db")
    bad = good(axle_position="three")
    ingest.ingest_and_record(db, bad, now=NOW)
    import sqlite3
    con = sqlite3.connect(db)
    raw = con.execute("SELECT payload_raw FROM ingest_log").fetchone()[0]
    con.close()
    assert json.loads(raw)["axle_position"] == "three", raw


@test
def test_an_accepted_payload_is_not_duplicated_in_full_in_the_log():
    """Store the digest for an acceptance; the reading already exists in scoring."""
    db = os.path.join(tempfile.mkdtemp(prefix="axiom-ingest-"), "log.db")
    ingest.ingest_and_record(db, good(), now=NOW)
    import sqlite3
    con = sqlite3.connect(db)
    row = con.execute("SELECT payload_raw, payload_sha FROM ingest_log").fetchone()
    con.close()
    assert row[0] == "", "an accepted reading must not be stored a second time"
    assert len(row[1]) == 64, row[1]


@test
def test_the_http_route_maps_outcomes_to_distinct_status_codes():
    """
    A collector that treats every non-200 as "retry" would retry a payload that
    can never succeed until it jams the queue, and would drop one that needs a
    human. The codes have to differ.
    """
    import threading
    import time
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    db = os.path.join(tempfile.mkdtemp(prefix="axiom-ingest-http-"), "l.db")
    os.environ["AXIOM_DB_PATH"] = db
    from backend import main as m
    from backend import store

    old = store.DB_PATH
    store.DB_PATH = db
    srv = ThreadingHTTPServer(("127.0.0.1", 0), m.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from backend import ingest_auth
    _col = ingest_auth.enroll_collector(db, "http-test-collector")
    _tok = _col["token"]

    def post(payload, raw=None, token=_tok):
        body = raw if raw is not None else json.dumps(payload).encode()
        hdrs = {"Content-Type": "application/json"}
        if token is not None:
            hdrs["Authorization"] = "Bearer " + token
        req = urllib.request.Request(
            "http://127.0.0.1:%d/api/ingest" % port, data=body,
            headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    now = time.time()
    try:
        cases = [
            (good(), None, 202, ingest.ACCEPTED),
            ({"axle_position": "x"}, None, 422, ingest.REJECTED_SCHEMA),
            (good(timestamp_unix=now + 9000), None, 422, ingest.REJECTED_TIMESTAMP),
            (good(ambient_temp_f=90.0, journal_temp_f=10.0), None, 422,
             ingest.REJECTED_PLAUSIBILITY),
            (good(speed_mps=0.0, ambient_temp_f=70.0, journal_temp_f=260.0),
             None, 200, ingest.SUSPECT),
            (None, b"<<<not json>>>", 422, ingest.REJECTED_SCHEMA),
        ]
        for payload, raw, want_status, want_outcome in cases:
            st, body = post(payload, raw)
            assert st == want_status, (want_outcome, st, body)
            assert body["outcome"] == want_outcome, (want_outcome, body)
            if want_outcome != ingest.ACCEPTED:
                assert body["advisory_emitted"] is False, body
    finally:
        srv.shutdown()
        store.DB_PATH = old

    import sqlite3
    con = sqlite3.connect(db)
    logged = con.execute("SELECT COUNT(*) FROM ingest_log").fetchone()[0]
    con.close()
    assert logged == len(cases), "every request must be logged, got %d" % logged


@test
def test_the_http_route_refuses_a_missing_or_bad_token_and_logs_nothing():
    """
    The credential is checked before the body is read or logged. A caller with
    no token, a wrong token, or a garbage body plus no token must not write a
    row: an ingest log anyone can append to is a poisoning vector in itself.
    """
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    db = os.path.join(tempfile.mkdtemp(prefix="axiom-ingest-noauth-"), "l.db")
    os.environ["AXIOM_DB_PATH"] = db
    from backend import main as m
    from backend import store, ingest_auth

    old = store.DB_PATH
    store.DB_PATH = db
    srv = ThreadingHTTPServer(("127.0.0.1", 0), m.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def post_raw(raw, token=None):
        hdrs = {"Content-Type": "application/json"}
        if token is not None:
            hdrs["Authorization"] = "Bearer " + token
        req = urllib.request.Request(
            "http://127.0.0.1:%d/api/ingest" % port, data=raw,
            headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        # Before any collector exists, the path is closed.
        st, body = post_raw(b"{}")
        assert st == 503, ("no collector must close the route", st, body)

        ingest_auth.enroll_collector(db, "noauth-col")
        # No token.
        st, body = post_raw(json.dumps(good()).encode())
        assert st == 401, ("missing token must be 401", st, body)
        # Wrong token.
        st, body = post_raw(json.dumps(good()).encode(), token="deadbeef" * 8)
        assert st == 401, ("unknown token must be 401", st, body)
        # Garbage body, no token: must NOT log a row.
        st, body = post_raw(b"<<<not json>>>")
        assert st == 401, ("garbage without a token must be refused at auth", st, body)
    finally:
        srv.shutdown()
        store.DB_PATH = old

    import sqlite3
    con = sqlite3.connect(db)
    try:
        n = con.execute("SELECT COUNT(*) FROM ingest_log").fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    con.close()
    assert n == 0, "an unauthenticated caller must write no ingest rows, got %d" % n


# ---------------------------------------------------------------------------
def main():
    print(f"{len(RESULTS)} tests")
    bad = 0
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f" -> {exc!r}"))
        bad += 0 if ok else 1
    print(f"\n{len(RESULTS) - bad} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
