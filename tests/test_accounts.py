"""
Tests for local accounts and authenticated sessions (AD-2, the entry half).

The claim under test is narrow: **a disposition can only be written by a caller
presenting a live session token, and the identity on the resulting row comes from
that session rather than from anything the caller typed.** These tests do not
assert that a human was at the keyboard; B01 §7 item 1 keeps that open by name.

Most tests below are attempts to get in without a credential, or to act as
somebody else: no token, a forged token, an expired token, a revoked token, a
token whose account was revoked after sign-in, a token whose certificate was
revoked after sign-in, and a passphrase guessed past the lockout.

Run: python3 -I tests/test_accounts.py
"""

import os
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_TMPDIR = tempfile.mkdtemp(prefix="axiom-accounts-test-")
os.environ.setdefault("AXIOM_DB_PATH", os.path.join(_TMPDIR, "test.db"))

from backend import accounts as acct  # noqa: E402
from backend import attribution as at  # noqa: E402

HOFFMAN_KEY = b"\xa1" * 32
OKAFOR_KEY = b"\xb2" * 32

RESULTS = []


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    return fn


def fresh():
    """Empty database with both registries, plus one enrolled reviewer."""
    if os.path.exists(acct_db_path()):
        os.remove(acct_db_path())
    acct.init(acct_db_path())
    at.register(acct_db_path(), "Hoffman", "CERT-H-1", HOFFMAN_KEY)
    acct.enroll(acct_db_path(), "hoffman", "correct horse battery",
                "CERT-H-1", iterations=1000)


def acct_db_path():
    return os.environ["AXIOM_DB_PATH"]


def expect_refusal(fn, contains=None):
    """Assert fn raises ValueError, optionally mentioning a phrase."""
    try:
        fn()
    except ValueError as exc:
        if contains is not None:
            assert contains in str(exc), \
                "refusal did not mention %r; it said %r" % (contains, str(exc))
        return str(exc)
    raise AssertionError("expected ValueError, got none")


# ---------------------------------------------------------------------------
# L1 — credential primitives. Literals, not round-trips.
# ---------------------------------------------------------------------------
@test
def test_pbkdf2_matches_published_sha256_vector():
    # PBKDF2-HMAC-SHA256, P="password", S="salt", c=1.
    # Independently confirmed with `openssl kdf -kdfopt digest:SHA256` at c=4096;
    # the c=1 and c=2 vectors are the standard published set.
    assert acct.derive_verifier("password", b"salt", 1) == (
        "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b")
    assert acct.derive_verifier("password", b"salt", 2) == (
        "ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c251dfd6e2d85a95474c43")


@test
def test_pbkdf2_matches_openssl_at_4096_iterations():
    assert acct.derive_verifier("password", b"salt", 4096) == (
        "c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a")


@test
def test_different_salt_gives_different_verifier():
    a = acct.derive_verifier("same passphrase", b"\x00" * 16, 1000)
    b = acct.derive_verifier("same passphrase", b"\x01" * 16, 1000)
    assert a != b, "salt must change the verifier or it is doing nothing"


@test
def test_different_iterations_give_different_verifier():
    a = acct.derive_verifier("pw", b"\x00" * 16, 1000)
    b = acct.derive_verifier("pw", b"\x00" * 16, 2000)
    assert a != b


@test
def test_empty_passphrase_is_refused():
    expect_refusal(lambda: acct.derive_verifier("", b"\x00" * 16, 1000),
                   "passphrase is required")


@test
def test_derive_verifier_refuses_an_empty_salt():
    expect_refusal(lambda: acct.derive_verifier("pw", b"", 1000),
                   "salt is required")


@test
def test_passphrase_comparison_is_constant_time():
    # Not a behavioural test, and it cannot be one: `==` and `hmac.compare_digest`
    # return the same answer for every input. The difference is timing, which a
    # unit test cannot see and an attacker on the local network can. So this
    # asserts the source uses the constant-time call. It is a regression guard
    # against a well-meant "simplification", and it says so rather than pretending
    # to prove timing safety. Confirmed by mutation 2026-11-11: swapping to `==`
    # left the whole behavioural suite green.
    src = open(os.path.join(ROOT, "backend", "accounts.py"), encoding="utf-8").read()
    assert "hmac.compare_digest(got, expected_hex)" in src, \
        "verify_passphrase no longer uses hmac.compare_digest"
    assert "got == expected_hex" not in src, \
        "verify_passphrase compares verifiers with ==, which is a timing oracle"


@test
def test_new_salt_is_the_policy_length_and_random():
    a = acct.new_salt()
    b = acct.new_salt()
    assert len(a) == acct.SALT_BYTES == 16, len(a)
    assert a != b, "two salts must not collide"


@test
def test_verify_passphrase_accepts_and_refuses():
    salt = acct.new_salt()
    v = acct.derive_verifier("right", salt, 1000)
    assert acct.verify_passphrase("right", salt.hex(), 1000, v) is True
    assert acct.verify_passphrase("wrong", salt.hex(), 1000, v) is False


@test
def test_verify_passphrase_refuses_malformed_stored_salt():
    # A corrupt salt column must be a refusal, not an exception escaping into the
    # request handler as a 500 with a traceback.
    assert acct.verify_passphrase("pw", "not-hex", 1000, "00" * 32) is False


@test
def test_token_digest_is_stable_and_differs_per_token():
    t1 = acct.mint_token()
    t2 = acct.mint_token()
    assert t1 != t2
    assert acct.token_digest(t1) == acct.token_digest(t1)
    assert acct.token_digest(t1) != acct.token_digest(t2)
    assert len(acct.token_digest(t1)) == 64


@test
def test_token_entropy_is_at_least_32_bytes():
    # token_urlsafe(32) is 43 chars of base64url over 32 random bytes.
    t = acct.mint_token()
    assert len(t) >= 43, len(t)


# ---------------------------------------------------------------------------
# L2 — enrollment
# ---------------------------------------------------------------------------
@test
def test_enroll_binds_to_the_registry_entry():
    fresh()
    live = [a for a in acct.accounts(acct_db_path()) if a["revoked_at"] is None]
    assert len(live) == 1, live
    assert live[0]["reviewer_name"] == "Hoffman"
    assert live[0]["cert_id"] == "CERT-H-1"
    assert live[0]["key_id"] == at.key_id(HOFFMAN_KEY)


@test
def test_enroll_withholds_the_verifier():
    # The stored hash must not appear in any return value or listing.
    fresh()
    for entry in acct.accounts(acct_db_path()):
        assert "verifier" not in entry, entry
        assert "salt" not in entry, entry


@test
def test_enroll_refuses_an_unregistered_certificate():
    fresh()
    expect_refusal(lambda: acct.enroll(acct_db_path(), "ghost", "pw", "CERT-NOPE",
                                       iterations=1000),
                   "not in the reviewer registry")


@test
def test_enroll_refuses_a_revoked_certificate():
    fresh()
    at.revoke(acct_db_path(), "Hoffman", note="left the company")
    expect_refusal(lambda: acct.enroll(acct_db_path(), "hoffman2", "pw",
                                       "CERT-H-1", iterations=1000),
                   "revoked")


@test
def test_enroll_refuses_duplicate_live_username():
    fresh()
    expect_refusal(lambda: acct.enroll(acct_db_path(), "hoffman", "other",
                                       "CERT-H-1", iterations=1000),
                   "already in use")


@test
def test_enroll_refuses_whitespace_and_at_in_username():
    fresh()
    expect_refusal(lambda: acct.enroll(acct_db_path(), "has space", "pw",
                                       "CERT-H-1", iterations=1000))
    expect_refusal(lambda: acct.enroll(acct_db_path(), "a@b", "pw",
                                       "CERT-H-1", iterations=1000))


@test
def test_enroll_refuses_empty_username():
    fresh()
    expect_refusal(lambda: acct.enroll(acct_db_path(), "   ", "pw", "CERT-H-1",
                                       iterations=1000))


# ---------------------------------------------------------------------------
# L2 — authentication
# ---------------------------------------------------------------------------
@test
def test_authenticate_accepts_the_right_passphrase():
    fresh()
    a = acct.authenticate(acct_db_path(), "hoffman", "correct horse battery")
    assert a["username"] == "hoffman"
    assert a["reviewer_name"] == "Hoffman"


@test
def test_authenticate_refuses_the_wrong_passphrase():
    fresh()
    expect_refusal(
        lambda: acct.authenticate(acct_db_path(), "hoffman", "wrong"),
        "do not match an account")


@test
def test_unknown_user_and_wrong_passphrase_say_the_same_thing():
    # Distinguishing them turns the sign-in form into a user directory.
    fresh()
    a = expect_refusal(
        lambda: acct.authenticate(acct_db_path(), "nobody", "pw"))
    b = expect_refusal(
        lambda: acct.authenticate(acct_db_path(), "hoffman", "wrong"))
    assert a == b, "the two refusals must be identical; got %r and %r" % (a, b)


@test
def test_lockout_after_threshold_failures():
    fresh()
    for _ in range(acct.LOCKOUT_THRESHOLD):
        try:
            acct.authenticate(acct_db_path(), "hoffman", "wrong")
        except ValueError:
            pass
    expect_refusal(
        lambda: acct.authenticate(acct_db_path(), "hoffman", "correct horse battery"),
        "too many failed sign-in attempts")


@test
def test_lockout_does_not_apply_to_a_different_account():
    fresh()
    at.register(acct_db_path(), "Okafor", "CERT-O-1", OKAFOR_KEY)
    acct.enroll(acct_db_path(), "okafor", "pw-okafor", "CERT-O-1", iterations=1000)
    for _ in range(acct.LOCKOUT_THRESHOLD):
        try:
            acct.authenticate(acct_db_path(), "hoffman", "wrong")
        except ValueError:
            pass
    a = acct.authenticate(acct_db_path(), "okafor", "pw-okafor")
    assert a["username"] == "okafor"


@test
def test_auth_events_are_written_and_append_only():
    fresh()
    try:
        acct.authenticate(acct_db_path(), "hoffman", "wrong")
    except ValueError:
        pass
    with sqlite3.connect(acct_db_path()) as conn:
        n = conn.execute("SELECT COUNT(*) FROM auth_events").fetchone()[0]
        assert n == 1, n
        try:
            conn.execute("DELETE FROM auth_events")
            raise AssertionError("auth log accepted a delete")
        except sqlite3.IntegrityError as exc:
            assert "append-only" in str(exc), exc


# ---------------------------------------------------------------------------
# L2 — sessions
# ---------------------------------------------------------------------------
@test
def test_issue_session_returns_a_token_that_resolves():
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    assert len(s["token"]) >= 43
    got = acct.resolve_session(acct_db_path(), s["token"])
    assert got["reviewer_name"] == "Hoffman"
    assert got["cert_id"] == "CERT-H-1"
    assert got["username"] == "hoffman"


@test
def test_session_stores_only_the_digest():
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    with sqlite3.connect(acct_db_path()) as conn:
        rows = conn.execute("SELECT token_hash FROM sessions").fetchall()
    stored = {r[0] for r in rows}
    assert s["token"] not in stored, "the raw token must never be stored"
    assert acct.token_digest(s["token"]) in stored


@test
def test_resolve_refuses_a_forged_token():
    fresh()
    acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), acct.mint_token()),
                   "not recognised")


@test
def test_resolve_refuses_an_empty_token():
    fresh()
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), ""),
                   "no session token")


@test
def test_resolve_refuses_an_expired_session():
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery",
                           ttl_seconds=1)
    with sqlite3.connect(acct_db_path()) as conn:
        conn.execute("UPDATE sessions SET expires_at = datetime('now','-1 minute') "
                     "WHERE id = ?", (s["session_id"],))
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), s["token"]),
                   "expired")


@test
def test_revoke_session_stops_it_immediately():
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    acct.revoke_session(acct_db_path(), s["token"])
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), s["token"]),
                   "revoked")


@test
def test_revoke_session_is_idempotent():
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    acct.revoke_session(acct_db_path(), s["token"])
    acct.revoke_session(acct_db_path(), s["token"])  # must not raise


@test
def test_revoke_session_refuses_an_unknown_token():
    fresh()
    expect_refusal(lambda: acct.revoke_session(acct_db_path(), acct.mint_token()),
                   "not recognised")


@test
def test_account_revocation_kills_live_sessions():
    # This is the one an appender gets wrong: the session row is untouched, and
    # only the account's *newest* row carries the revocation.
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    acct.revoke_account(acct_db_path(), "hoffman", note="left the company")
    # `revoke_account` revokes the account's live sessions in the same
    # transaction, so the session check fires first and says "revoked". Either
    # refusal is correct — what must not happen is a working session. The
    # separate "account behind this session" branch is exercised directly below.
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), s["token"]),
                   "revoked")


@test
def test_account_revocation_is_caught_even_if_the_session_row_survives():
    # Reach the account-level branch: revoke the account, then un-revoke the
    # session row as a host owner with database access could. The session must
    # still be refused, because the account behind it is gone.
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    acct.revoke_account(acct_db_path(), "hoffman", note="left the company")
    with sqlite3.connect(acct_db_path()) as conn:
        conn.execute("UPDATE sessions SET revoked_at = NULL WHERE id = ?",
                     (s["session_id"],))
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), s["token"]),
                   "account behind this session has been revoked")


@test
def test_account_revocation_blocks_sign_in():
    fresh()
    acct.revoke_account(acct_db_path(), "hoffman")
    expect_refusal(lambda: acct.authenticate(acct_db_path(), "hoffman",
                                             "correct horse battery"),
                   "do not match an account")


@test
def test_account_revocation_then_reenrollment_of_the_same_name():
    # A revoked account must be replaceable by a newly issued certificate, or a
    # returning reviewer is locked out of the product forever.
    fresh()
    acct.revoke_account(acct_db_path(), "hoffman")
    at.revoke(acct_db_path(), "Hoffman", note="cert superseded")
    at.register(acct_db_path(), "Hoffman", "CERT-H-2", b"\xc3" * 32)
    a = acct.enroll(acct_db_path(), "hoffman", "new passphrase", "CERT-H-2",
                    iterations=1000)
    assert a["cert_id"] == "CERT-H-2"
    got = acct.issue_session(acct_db_path(), "hoffman", "new passphrase")
    assert got["cert_id"] == "CERT-H-2"


@test
def test_certificate_revocation_after_sign_in_blocks_the_session():
    # resolve_session check 5: the expensive one to omit.
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    at.revoke(acct_db_path(), "Hoffman", note="cert withdrawn")
    expect_refusal(lambda: acct.resolve_session(acct_db_path(), s["token"]),
                   "certification behind this session has been revoked")


@test
def test_certificate_revocation_after_sign_in_blocks_new_sessions():
    fresh()
    s = acct.issue_session(acct_db_path(), "hoffman", "correct horse battery")
    at.revoke(acct_db_path(), "Hoffman", note="cert withdrawn")
    expect_refusal(lambda: acct.issue_session(acct_db_path(), "hoffman",
                                              "correct horse battery"),
                   "revoked")
    assert acct.token_digest(s["token"])


@test
def test_session_ttl_must_be_positive():
    fresh()
    expect_refusal(lambda: acct.issue_session(acct_db_path(), "hoffman",
                                              "correct horse battery",
                                              ttl_seconds=0))


# ---------------------------------------------------------------------------
# L2 — the account register's integrity
# ---------------------------------------------------------------------------
@test
def test_account_register_verifies_when_untouched():
    fresh()
    r = acct.verify_accounts(acct_db_path())
    assert r["ok"] is True, r
    assert r["entries"] == 1, r


@test
def test_swapping_a_verifier_breaks_the_chain():
    # A host owner who can swap a verifier owns the account. The chain must say so.
    fresh()
    with sqlite3.connect(acct_db_path()) as conn:
        conn.execute("DROP TRIGGER accounts_no_update")
        conn.execute("UPDATE accounts SET verifier = ? WHERE id = 1",
                     ("00" * 32,))
    r = acct.verify_accounts(acct_db_path())
    assert r["ok"] is False, r
    assert any("does not hash" in p["problem"] for p in r["problems"]), r


@test
def test_register_refuses_update_and_delete():
    fresh()
    with sqlite3.connect(acct_db_path()) as conn:
        for stmt, word in (("UPDATE accounts SET note='x'", "append-only"),
                           ("DELETE FROM accounts", "append-only")):
            try:
                conn.execute(stmt)
                raise AssertionError("%s was permitted" % stmt)
            except sqlite3.IntegrityError as exc:
                assert word in str(exc), exc


@test
def test_register_refuses_insert_or_replace():
    fresh()
    with sqlite3.connect(acct_db_path()) as conn:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO accounts (id, username, reviewer_name, "
                "cert_id, key_id, salt, iterations, verifier, created_at, "
                "prev_hash, entry_hash) VALUES (1,'x','x','x','x','00',1,'00',"
                "'now','00','00')")
            raise AssertionError("INSERT OR REPLACE was permitted")
        except sqlite3.IntegrityError as exc:
            assert "append-only" in str(exc), exc


if __name__ == "__main__":
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else " -> %s" % exc))
    print("\n%d passed, %d failed" % (passed, failed))
    sys.exit(1 if failed else 0)
