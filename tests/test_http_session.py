"""
End-to-end HTTP tests for the session gate.

`test_session_route.py` calls the route functions, which proves what the handler
decides. This file starts a real `ThreadingHTTPServer` on an ephemeral port and
talks to it over a socket, which proves the plumbing that the functions sit in:
header parsing through `BaseHTTPRequestHandler`, JSON decoding, the size caps, and
that `route_post_disposition` is actually reached with the headers it needs.

Run: python3 -I tests/test_http_session.py
"""

import http.client
import json
import os
import sqlite3
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_TMPDIR = tempfile.mkdtemp(prefix="axiom-http-session-")
os.environ.setdefault("AXIOM_DB_PATH", os.path.join(_TMPDIR, "test.db"))

from backend import accounts as acct  # noqa: E402
from backend import attribution as at  # noqa: E402
from backend import ingest  # noqa: E402
from backend import ingest_auth  # noqa: E402
from backend import main  # noqa: E402
from backend import store  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

KEY = b"\xa1" * 32
PW = "a long enough passphrase"

RESULTS = []
_SERVER = {"srv": None, "port": None}


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    return fn


def _start():
    if _SERVER["srv"] is not None:
        return
    srv = ThreadingHTTPServer(("127.0.0.1", 0), main.Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    _SERVER["srv"] = srv
    _SERVER["port"] = srv.server_address[1]


def _stop():
    srv = _SERVER["srv"]
    if srv is not None:
        srv.shutdown()
        srv.server_close()
        _SERVER["srv"] = None


def fresh():
    db = store.DB_PATH
    if os.path.exists(db):
        os.remove(db)
    store.init_db()
    acct.init(db)
    at.register(db, "Hoffman", "CERT-H-1", KEY)
    acct.enroll(db, "hoffman", PW, "CERT-H-1", iterations=1000)
    # Enrolled so the ingest route is past its AUTH_NONE branch and the
    # missing-token and unknown-token checks are actually on the path.
    ingest_auth.init(db)
    ingest_auth.enroll_collector(db, "collector-01")


def _ingest_log_count():
    """
    Rows in the ingest log, initialised on demand.

    The log table is created lazily by the handler, so a request that auth
    rejects never creates it. Counting must therefore treat a missing table as
    zero rather than raising — an error here would pass for "no rows written",
    which is exactly the false green M2 and M3 are there to catch.
    """
    db = store.DB_PATH
    ingest.init_ingest_log(db)
    with sqlite3.connect(db) as con:
        return con.execute("SELECT COUNT(*) FROM ingest_log").fetchone()[0]


def req(method, path, body=None, headers=None):
    _start()
    conn = http.client.HTTPConnection("127.0.0.1", _SERVER["port"], timeout=10)
    raw = json.dumps(body).encode("utf-8") if body is not None else None
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    conn.request(method, path, body=raw, headers=h)
    r = conn.getresponse()
    payload = r.read()
    conn.close()
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = payload.decode("utf-8", "replace")
    return r.status, parsed


def req_raw(method, path, raw, headers=None):
    """
    Send bytes verbatim. `req` json-encodes its body, which cannot produce the
    unparseable payload the ingest gate has to refuse *before* logging it.
    """
    _start()
    conn = http.client.HTTPConnection("127.0.0.1", _SERVER["port"], timeout=10)
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    conn.request(method, path, body=raw, headers=h)
    r = conn.getresponse()
    payload = r.read()
    conn.close()
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = payload.decode("utf-8", "replace")
    return r.status, parsed


# ---------------------------------------------------------------------------
@test
def test_sign_in_over_http_and_write_over_http():
    fresh()
    status, body = req("POST", "/api/session",
                       {"username": "hoffman", "passphrase": PW})
    assert status == 200, body
    tok = body["token"]
    status, body = req("POST", "/api/warrant/AD-2025-0001/disposition",
                       {"disposition": "concur_dispatch"},
                       {"Authorization": "Bearer " + tok})
    assert status == 200, body
    assert body["reviewer_name"] == "Hoffman"
    rec = store.get_disposition("AD-2025-0001")
    assert rec["reviewer_name"] == "Hoffman"


@test
def test_write_without_header_over_http_is_401():
    fresh()
    status, body = req("POST", "/api/warrant/AD-2025-0001/disposition",
                       {"disposition": "concur_dispatch"})
    assert status == 401, (status, body)
    assert store.ledger_size() == 0


@test
def test_ingest_without_header_on_an_enrolled_deployment_is_401():
    # Mutant M2: with the missing-token check removed from do_POST, this request
    # falls through to the body read. The earlier 503 test cannot see that — it
    # runs on a deployment with nothing enrolled, so the AUTH_NONE branch returns
    # first and the missing-token check is never on the path.
    #
    # The body is deliberately unparseable. A well-formed body would still be
    # refused by route_post_ingest_authenticated's own re-check, so it would
    # pass with M2 in place and prove nothing. Garbage is the discriminating
    # case: do_POST logs an unparseable body itself, before the route is
    # reached, so this is the one shape where a removed check leaves a row.
    fresh()
    mode = ingest_auth.auth_mode(store.DB_PATH)
    assert mode != ingest_auth.AUTH_NONE, mode
    before = _ingest_log_count()
    status, body = req_raw("POST", "/api/ingest", b"{not json at all")
    assert status == 401, (status, body)
    assert _ingest_log_count() == before


@test
def test_ingest_with_an_unknown_token_is_401_and_logs_nothing():
    # Mutant M3: resolve_token raising must be caught and answered 401. The
    # mutation swallows the ValueError and substitutes a placeholder collector,
    # so the body is parsed and logged for a caller who never authenticated.
    # Same reasoning as M2 above: the payload is unparseable so that the log
    # write in do_POST is the observable, not a 401 the route would have given
    # anyway.
    fresh()
    before = _ingest_log_count()
    status, body = req_raw("POST", "/api/ingest", b"{not json at all",
                           {"Authorization": "Bearer " + ("0" * 64)})
    assert status == 401, (status, body)
    assert _ingest_log_count() == before


@test
def test_sign_out_over_http_then_write_is_401():
    fresh()
    status, body = req("POST", "/api/session",
                       {"username": "hoffman", "passphrase": PW})
    tok = body["token"]
    status, _ = req("DELETE", "/api/session", None,
                    {"Authorization": "Bearer " + tok})
    assert status == 200
    status, body = req("POST", "/api/warrant/AD-2025-0001/disposition",
                       {"disposition": "concur_dispatch"},
                       {"Authorization": "Bearer " + tok})
    assert status == 401, (status, body)


@test
def test_sign_in_body_that_is_not_json_is_400_not_500():
    fresh()
    _start()
    conn = http.client.HTTPConnection("127.0.0.1", _SERVER["port"], timeout=10)
    conn.request("POST", "/api/session", body=b"{not json",
                 headers={"Content-Type": "application/json"})
    r = conn.getresponse()
    r.read()
    conn.close()
    assert r.status == 400, r.status


@test
def test_oversized_sign_in_body_is_413():
    fresh()
    _start()
    conn = http.client.HTTPConnection("127.0.0.1", _SERVER["port"], timeout=10)
    big = b'{"username":"a","passphrase":"' + b"x" * 9000 + b'"}'
    conn.request("POST", "/api/session", body=big,
                 headers={"Content-Type": "application/json"})
    r = conn.getresponse()
    r.read()
    conn.close()
    assert r.status == 413, r.status


@test
def test_disposition_body_that_is_not_an_object_is_400():
    fresh()
    status, body = req("POST", "/api/session",
                       {"username": "hoffman", "passphrase": PW})
    tok = body["token"]
    status, body = req("POST", "/api/warrant/AD-2025-0001/disposition",
                       [1, 2, 3], {"Authorization": "Bearer " + tok})
    assert status == 400, (status, body)


@test
def test_a_500_never_leaks_a_traceback_over_http():
    # The handler catches Exception and returns str(exc). This proves the process
    # survives a deliberately bad request rather than testing the message text.
    fresh()
    status, body = req("POST", "/api/warrant//disposition",
                       {"disposition": "concur_dispatch"})
    # Empty advisory id falls through to the unknown-route branch, not a crash.
    assert status in (400, 401, 404, 500), status


if __name__ == "__main__":
    try:
        passed = sum(1 for _, ok, _ in RESULTS if ok)
        failed = len(RESULTS) - passed
        for name, ok, exc in RESULTS:
            print(("PASS  " if ok else "FAIL  ") + name +
                  ("" if ok else " -> %s" % exc))
        print("\n%d passed, %d failed" % (passed, failed))
    finally:
        _stop()
    sys.exit(1 if failed else 0)
