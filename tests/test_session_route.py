"""
Tests for the authenticated disposition route (AD-2, the entry half).

These call the route functions directly rather than going through the socket, so
they test the gate itself: what the handler decides before any transcript is
written. The one thing they cannot cover is the HTTP plumbing in
`Handler.do_POST` — that is exercised by `test_http_session.py`.

The claim under test: **a disposition cannot be written without a live session,
and the identity on the row comes from that session.** Most tests below are
attempts to write one anyway: no header, a bogus header, a forged token, an
expired token, a signed-out token, a revoked account, a revoked certificate, and
a body that names the reviewer directly.

Run: python3 -I tests/test_session_route.py
"""

import os
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_TMPDIR = tempfile.mkdtemp(prefix="axiom-session-route-")
os.environ.setdefault("AXIOM_DB_PATH", os.path.join(_TMPDIR, "test.db"))

from backend import accounts as acct  # noqa: E402
from backend import attribution as at  # noqa: E402
from backend import main  # noqa: E402
from backend import store  # noqa: E402

KEY_H = b"\xa1" * 32
KEY_O = b"\xb2" * 32
PW_H = "correct horse battery"
PW_O = "another long passphrase"

RESULTS = []


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    return fn


def fresh():
    db = store.DB_PATH
    if os.path.exists(db):
        os.remove(db)
    store.init_db()
    acct.init(db)
    at.register(db, "Hoffman", "CERT-H-1", KEY_H)
    at.register(db, "Okafor", "CERT-O-1", KEY_O)
    acct.enroll(db, "hoffman", PW_H, "CERT-H-1", iterations=1000)
    acct.enroll(db, "okafor", PW_O, "CERT-O-1", iterations=1000)


def sign_in(username, pw):
    body, status = main.route_post_session({"username": username,
                                            "passphrase": pw})
    assert status == 200, (status, body)
    return body["token"]


def hdr(token, key=KEY_H):
    """Session token plus the reviewer key entry now requires."""
    import base64
    h = {"X-Reviewer-Key": base64.b64encode(key).decode()}
    if token:
        h["Authorization"] = "Bearer " + token
    return h


def post(advisory, body, token=None, key=KEY_H):
    return main.route_post_disposition(advisory, body, hdr(token, key))


# ---------------------------------------------------------------------------
# Sign-in
# ---------------------------------------------------------------------------
@test
def test_sign_in_returns_a_token_and_the_bound_identity():
    fresh()
    body, status = main.route_post_session({"username": "hoffman",
                                            "passphrase": PW_H})
    assert status == 200, body
    assert body["token"]
    assert body["reviewer_name"] == "Hoffman"
    assert body["cert_id"] == "CERT-H-1"
    assert "passphrase" not in body and "verifier" not in body


@test
def test_sign_in_refusal_is_401_and_does_not_reveal_which_half_was_wrong():
    fresh()
    b1, s1 = main.route_post_session({"username": "hoffman",
                                      "passphrase": "wrong"})
    b2, s2 = main.route_post_session({"username": "nobody",
                                      "passphrase": "wrong"})
    assert s1 == s2 == 401
    assert b1["error"] == b2["error"], (b1, b2)


@test
def test_sign_in_requires_both_fields():
    fresh()
    _, s = main.route_post_session({"username": "hoffman"})
    assert s == 400


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
@test
def test_no_token_is_refused_401():
    fresh()
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"})
    assert status == 401, (status, body)
    assert "authentication required" in body["error"]
    assert store.ledger_size() == 0


@test
def test_no_account_anywhere_closes_the_path_with_503():
    # Fail closed. The tempting design is to keep the old free-text behaviour
    # when no account exists so a fresh demo works; then the gate is only as
    # good as somebody remembering to enroll.
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"})
    assert status == 503, (status, body)
    assert body["auth_mode"] == acct.AUTH_NONE
    assert store.ledger_size() == 0


@test
def test_valid_token_writes_a_row_naming_the_session_reviewer():
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch",
                                         "note": "inspect at next terminal"}, tok)
    assert status == 200, (status, body)
    assert body["reviewer_name"] == "Hoffman"
    assert body["cert_id"] == "CERT-H-1"
    rec = store.get_disposition("AD-2025-0001")
    assert rec["reviewer_name"] == "Hoffman"
    assert rec["cert_id"] == "CERT-H-1"


@test
def test_body_carrying_reviewer_name_is_refused_not_ignored():
    # The important property: an integrator whose field is silently dropped will
    # believe it was honoured.
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch",
                                         "reviewer_name": "Okafor"}, tok)
    assert status == 400, (status, body)
    assert "reviewer_name" in body["error"]
    assert store.ledger_size() == 0


@test
def test_body_carrying_cert_id_is_refused_not_ignored():
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch",
                                         "cert_id": "CERT-O-1"}, tok)
    assert status == 400, (status, body)
    assert store.ledger_size() == 0


@test
def test_forged_token_is_refused():
    fresh()
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"},
                        acct.mint_token())
    assert status == 401, (status, body)


@test
def test_expired_token_is_refused():
    fresh()
    tok = sign_in("hoffman", PW_H)
    with sqlite3.connect(store.DB_PATH) as conn:
        conn.execute("UPDATE sessions SET expires_at = datetime('now','-1 minute')")
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 401, (status, body)
    assert "expired" in body["error"]


@test
def test_signed_out_token_is_refused():
    fresh()
    tok = sign_in("hoffman", PW_H)
    main.route_delete_session(hdr(tok))
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 401, (status, body)


@test
def test_revoked_account_cannot_write():
    fresh()
    tok = sign_in("hoffman", PW_H)
    acct.revoke_account(store.DB_PATH, "hoffman")
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 401, (status, body)
    assert store.ledger_size() == 0


@test
def test_revoked_certificate_cannot_write():
    fresh()
    tok = sign_in("hoffman", PW_H)
    at.revoke(store.DB_PATH, "Hoffman", note="cert withdrawn")
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 401, (status, body)
    assert store.ledger_size() == 0


@test
def test_revocation_between_resolve_and_write_is_caught_by_the_lock_guard():
    # The race the guard in save_disposition exists for: resolve succeeds, the
    # certificate is revoked, then the write is attempted. Simulated by revoking
    # after a successful resolve inside route_post_disposition is impractical;
    # instead drive save_disposition directly with a guard that always refuses,
    # which is the exact code path and the exact refusal.
    fresh()
    before = store.ledger_size()

    def refuse():
        raise ValueError("certification revoked under the write lock")

    try:
        store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                               "concur_dispatch", guard=refuse)
    except ValueError as exc:
        assert "write lock" in str(exc)
    else:
        raise AssertionError("the guard did not abort the append")
    assert store.ledger_size() == before, "the guard did not roll the append back"


@test
def test_revocation_in_the_resolve_to_write_window_aborts_through_the_real_guard():
    # THE test the audit said was missing. The earlier version of this file
    # simulated the race with a guard that *raised*, which is not the guard the
    # route installs. The route's guard is `lambda: cert_is_live(...)` — it
    # *returns a bool* — and `save_disposition` discarded the return value, so the
    # guard computed False and the row was written anyway. 310 green tests.
    #
    # This drives the real route and revokes the certificate inside
    # `resolve_session`, i.e. exactly between the resolve and the write.
    fresh()
    tok = sign_in("hoffman", PW_H)

    real_resolve = acct.resolve_session

    def resolve_then_revoke(db_path, token):
        out = real_resolve(db_path, token)          # cert live at resolve
        at.revoke(db_path, "Hoffman", note="revoked in the window")
        return out                                   # dead by the time we write

    acct.resolve_session = resolve_then_revoke
    try:
        body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    finally:
        acct.resolve_session = real_resolve

    assert status == 401, "a disposition was written under a revoked certificate: %s" % (body,)
    assert store.ledger_size() == 0, "the aborted append left a row behind"


@test
def test_a_falsy_guard_aborts_the_append():
    # The minimal statement of the defect, independent of the route: a guard that
    # returns False must stop the write, because that is what the route passes.
    fresh()
    try:
        store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                               "concur_dispatch", guard=lambda: False)
    except ValueError as exc:
        assert "write guard refused" in str(exc), exc
    else:
        raise AssertionError("a guard returning False did not abort the append")
    assert store.ledger_size() == 0


@test
def test_a_truthy_guard_permits_the_append():
    # ...and the positive case, so the test above is not satisfied by a guard
    # that refuses everything.
    fresh()
    rec = store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                                 "concur_dispatch", guard=lambda: True)
    assert rec["id"] == 1
    assert store.ledger_size() == 1


@test
def test_guard_refusal_rolls_back_the_whole_transaction():
    # And the chain is untouched: no orphan row, no forked prev_hash.
    fresh()
    store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                           "concur_dispatch")
    head = store.verify_chain()
    assert head["ok"] is True, head
    try:
        store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                               "reject_sensor",
                               guard=lambda: (_ for _ in ()).throw(
                                   ValueError("nope")))
    except ValueError:
        pass
    assert store.ledger_size() == 1
    assert store.verify_chain()["ok"] is True


@test
def test_two_reviewers_write_under_their_own_names():
    fresh()
    th = sign_in("hoffman", PW_H)
    to = sign_in("okafor", PW_O)
    b1, s1 = post("AD-2025-0001", {"disposition": "concur_dispatch"}, th)
    b2, s2 = post("AD-2025-0001", {"disposition": "reject_sensor"}, to,
                  key=KEY_O)
    assert (s1, s2) == (200, 200), (b1, b2)
    hist = store.disposition_history("AD-2025-0001")
    assert [r["reviewer_name"] for r in hist] == ["Hoffman", "Okafor"]
    assert hist[1]["supersedes_id"] == hist[0]["id"]


@test
def test_entry_without_a_reviewer_key_is_401_and_writes_nothing():
    """A session alone is not an attestation. D09 §8.4."""
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = main.route_post_disposition(
        "AD-2025-0001", {"disposition": "concur_dispatch"},
        {"Authorization": "Bearer " + tok})
    assert status == 401, (status, body)
    # "reviewer key" appears in the unregistered-key message too, so asserting
    # that substring let this test pass with the early return removed (found by
    # mutation, M1). The distinguishing phrase is the header instruction.
    assert "reviewer key required" in body["error"]
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_another_reviewers_key_is_refused_and_writes_nothing():
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"},
                        tok, key=KEY_O)
    assert status == 401, (status, body)
    # The inner transactional guard also names both reviewers, so asserting the
    # two names let this pass with the route's early check removed (mutation M2).
    # The phrase below exists only in the route's message.
    assert "a reviewer signs decisions with their own key" in body["error"]
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_an_unregistered_key_is_refused():
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"},
                        tok, key=b"\x00" * 32)
    assert status == 401, (status, body)
    assert "not in the reviewer registry" in body["error"]
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_a_revoked_key_is_refused():
    fresh()
    tok = sign_in("hoffman", PW_H)
    at.revoke(store.DB_PATH, "Hoffman")
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 401, (status, body)
    assert "revoked" in body["error"]
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_a_key_registered_under_another_certificate_is_refused():
    """
    A stale key after renewal. Same reviewer, wrong certificate — the one case
    the reviewer-name check cannot see, because the name matches.
    """
    fresh()
    tok = sign_in("hoffman", PW_H)
    old = b"\xc3" * 32
    at.register(store.DB_PATH, "Hoffman", "CERT-H-0", old)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"},
                        tok, key=old)
    assert status == 401, (status, body)
    assert "CERT-H-0" in body["error"] and "CERT-H-1" in body["error"]
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_a_malformed_key_header_is_refused_not_half_parsed():
    fresh()
    tok = sign_in("hoffman", PW_H)
    for junk in ("!!!not-base64!!!", "   ", "a"):
        body, status = main.route_post_disposition(
            "AD-2025-0001", {"disposition": "concur_dispatch"},
            {"Authorization": "Bearer " + tok, "X-Reviewer-Key": junk})
        assert status == 401, (junk, status, body)
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_a_successful_write_carries_a_verifiable_attestation():
    """
    The point of the whole change: the row is written *with* its attestation in
    one transaction, and the attestation recomputes against the registry.
    """
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 200, (status, body)
    assert body["attestation"]["key_id"] == at.key_id(KEY_H)
    rows = store.disposition_history("AD-2025-0001")
    assert len(rows) == 1
    got = at.attestations(store.DB_PATH)
    assert got[rows[0]["id"]]["key_id"] == at.key_id(KEY_H)
    # Recomputed from the row and the key, not merely stored.
    assert got[rows[0]["id"]]["value"] == at.attestation_value(KEY_H, rows[0])
    assert at.verify_attestations(store.DB_PATH)["ok"] is True


@test
def test_the_attestation_is_written_with_the_row_or_not_at_all():
    """
    A refused key must leave the ledger untouched — not a row with no
    attestation, which would export as an honest-looking unattested record.
    """
    fresh()
    tok = sign_in("hoffman", PW_H)
    post("AD-2025-0001", {"disposition": "reject_sensor"}, tok, key=KEY_O)
    assert store.disposition_history("AD-2025-0001") == []
    assert at.attestations(store.DB_PATH) == {}
    assert store.verify_chain()["ok"] is True


@test
def test_malformed_authorization_headers_are_all_refused():
    fresh()
    tok = sign_in("hoffman", PW_H)
    for raw in (tok, "Bearer", "Bearer  " + tok, "Basic " + tok,
                "Bearer " + tok + ",", "bearer" + tok):
        body, status = main.route_post_disposition(
            "AD-2025-0001", {"disposition": "concur_dispatch"},
            {"Authorization": raw})
        assert status == 401, "header %r was accepted: %s" % (raw, body)
    # And the correctly formed one is accepted, so the test is not vacuous.
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    assert status == 200, body


@test
def test_identity_field_refusal_and_session_read_are_independently_load_bearing():
    # Two guards, one visible behaviour. Mutating *either alone* leaves the suite
    # green: if the body field is accepted but never read, the row is still right;
    # if it is read but the field is refused, the request never reaches the read.
    # Mutating both together is what turns a test red. Recorded here rather than
    # removing either guard — the refusal is what tells an integrator, and the
    # session read is what makes the refusal a defence rather than a courtesy.
    # Confirmed by mutation 2026-11-11: M5 alone survived, M5b (both) killed.
    src = open(os.path.join(ROOT, "backend", "main.py"), encoding="utf-8").read()
    assert 'for forbidden in ("reviewer_name", "cert_id"):' in src
    assert 'reviewer_name = session["reviewer_name"]' in src
    assert 'reviewer_name = (body.get("reviewer_name")' not in src


@test
def test_invalid_disposition_is_refused_after_authentication():
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "burn_it_down"}, tok)
    assert status == 400, (status, body)
    assert store.ledger_size() == 0


@test
def test_long_note_is_refused():
    fresh()
    tok = sign_in("hoffman", PW_H)
    body, status = post("AD-2025-0001", {"disposition": "concur_dispatch",
                                         "note": "x" * 501}, tok)
    assert status == 400, (status, body)


@test
def test_non_string_note_is_400_not_500():
    # The audit found `{"note": {...}}` raised AttributeError on .strip() and the
    # handler turned it into a 500. A malformed client request is the client's
    # fault and must say so.
    fresh()
    tok = sign_in("hoffman", PW_H)
    for bad in ({"a": 1}, [1, 2], 7, True):
        body, status = post("AD-2025-0001", {"disposition": "concur_dispatch",
                                             "note": bad}, tok)
        assert status == 400, "note=%r gave %s: %s" % (bad, status, body)
    assert store.ledger_size() == 0


@test
def test_hostile_body_shapes_never_cause_a_500():
    fresh()
    tok = sign_in("hoffman", PW_H)
    shapes = [
        {}, {"disposition": None}, {"disposition": ["concur_dispatch"]},
        {"disposition": "concur_dispatch", "note": {"deep": {"er": 1}}},
        {"disposition": "CONCUR_DISPATCH"}, {"disposition": " concur_dispatch"},
    ]
    accepted = 0
    for shape in shapes:
        body, status = post("AD-2025-0001", shape, tok)
        assert status in (200, 400), "shape %r gave %s: %s" % (shape, status, body)
        if status == 200:
            accepted += 1
    # Every shape in that list is malformed on purpose, including the
    # " concur_dispatch" one, which is refused because a leading space is not
    # stripped from the disposition. So the whole point is the status: none of
    # these is a 500. This test changed twice while being written — first the
    # expectation was one acceptance, then two — and both times the code was
    # right and the test was wrong. The list is the assertion.
    assert accepted == 0, "%d hostile shapes were accepted" % accepted


@test
def test_get_history_still_needs_no_auth():
    # Reading the decision trail is a review activity and is deliberately open on
    # the demo host; only the *write* is gated. Stated here so the asymmetry is a
    # decision on the record rather than an oversight.
    fresh()
    tok = sign_in("hoffman", PW_H)
    post("AD-2025-0001", {"disposition": "concur_dispatch"}, tok)
    body, status = main.route_get_disposition_history("AD-2025-0001")
    assert status == 200 and body["count"] == 1, body


# ---------------------------------------------------------------------------
# The transactional layer, tested on its own.
#
# The route checks the key early so a doomed request never opens a write
# transaction. That early check means every route-level test is refused *before*
# the in-transaction check runs, which made two mutations in
# `attribution.stamp_attestation` survive: the reviewer check and the revocation
# check could both be deleted with the route-level tests still green. Both layers
# are wanted — the early one for a clean refusal, the inner one because it holds
# the ledger's write lock and is the only place "still live" and "still unwritten"
# are true together. The tests below call store.save_disposition directly, with
# the route out of the way, so each inner check has to stand on its own.
# ---------------------------------------------------------------------------
@test
def test_the_transactional_attestation_refuses_a_mismatched_reviewer():
    fresh()
    with_key = lambda conn, rec: at.stamp_attestation(conn, rec, KEY_O)
    try:
        store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                               "concur_dispatch", attest=with_key)
    except ValueError as exc:
        assert "registered to" in str(exc), exc
    else:
        raise AssertionError("a key registered to another reviewer was accepted")
    assert store.disposition_history("AD-2025-0001") == []
    assert at.attestations(store.DB_PATH) == {}


@test
def test_the_transactional_attestation_refuses_a_revoked_key():
    fresh()
    at.revoke(store.DB_PATH, "Hoffman")
    with_key = lambda conn, rec: at.stamp_attestation(conn, rec, KEY_H)
    try:
        store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                               "concur_dispatch", attest=with_key)
    except ValueError as exc:
        assert "revoked" in str(exc), exc
    else:
        raise AssertionError("a revoked key was accepted")
    assert store.disposition_history("AD-2025-0001") == []


@test
def test_the_transactional_attestation_refuses_a_certificate_mismatch():
    fresh()
    old = b"\xc3" * 32
    at.register(store.DB_PATH, "Hoffman", "CERT-H-0", old)
    with_key = lambda conn, rec: at.stamp_attestation(conn, rec, old)
    try:
        store.save_disposition("AD-2025-0001", "Hoffman", "CERT-H-1",
                               "concur_dispatch", attest=with_key)
    except ValueError as exc:
        assert "certificate" in str(exc), exc
    else:
        raise AssertionError("a key for a stale certificate was accepted")
    assert store.disposition_history("AD-2025-0001") == []


if __name__ == "__main__":
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else " -> %s" % exc))
    print("\n%d passed, %d failed" % (passed, failed))
    sys.exit(1 if failed else 0)
