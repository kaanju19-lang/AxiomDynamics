"""Tests for ingest collector authentication (B01 §7 item 5).

A collector is not a reviewer. These tests pin the properties that follow from
that: a token is issued once and only its digest is stored, an enrollment's
revocation does not retroactively break a running collector, and the chain that
records both is append-only and tamper-evident.

Run: python3 -I tests/test_ingest_auth.py
"""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend import ingest_auth  # noqa: E402

RESULTS = []


def test(fn):
    try:
        fn()
    except AssertionError as exc:
        RESULTS.append((fn.__name__, False, exc))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    else:
        RESULTS.append((fn.__name__, True, None))
    return fn


class _Tmp:
    def __enter__(self):
        self.d = tempfile.mkdtemp()
        self.db = os.path.join(self.d, "t.db")
        return self.db

    def __exit__(self, *a):
        for p in (self.db, self.db + "-journal", self.db + "-wal",
                  self.db + "-shm"):
            if os.path.exists(p):
                os.remove(p)
        if os.path.isdir(self.d):
            os.rmdir(self.d)
        return False


@test
def test_enroll_returns_a_64_hex_token():
    with _Tmp() as db:
        r = ingest_auth.enroll_collector(db, "col-1")
        assert len(r["token"]) == 64, r["token"]
        assert all(c in "0123456789abcdef" for c in r["token"]), r["token"]
        assert r["name"] == "col-1"
        assert r["id"] >= 1


@test
def test_only_the_digest_reaches_the_database():
    with _Tmp() as db:
        r = ingest_auth.enroll_collector(db, "col-2")
        with open(db, "rb") as f:
            blob = f.read()
        assert r["token"].encode() not in blob, "the plaintext token was stored"
        assert ingest_auth.token_digest(r["token"]).encode() in blob


@test
def test_a_token_resolves_to_its_collector():
    with _Tmp() as db:
        r = ingest_auth.enroll_collector(db, "col-3")
        got = ingest_auth.resolve_token(db, r["token"])
        assert got["collector_id"] == r["id"]
        assert got["collector_name"] == "col-3"


@test
def test_an_unknown_token_is_refused():
    with _Tmp() as db:
        try:
            ingest_auth.resolve_token(db, "f" * 64)
            assert False, "an unknown token must not resolve"
        except ValueError as e:
            assert "not recognised" in str(e), e


@test
def test_an_empty_token_is_refused():
    with _Tmp() as db:
        try:
            ingest_auth.resolve_token(db, "")
            assert False, "an empty token must not resolve"
        except ValueError as e:
            assert "no ingest token" in str(e), e


@test
def test_a_revoked_enrollment_keeps_its_issued_token_live():
    """Deliberate: a collector is scheduled software, not a person who left."""
    with _Tmp() as db:
        r = ingest_auth.enroll_collector(db, "col-4")
        ingest_auth.revoke_collector(db, "col-4")
        got = ingest_auth.resolve_token(db, r["token"])
        assert got["collector_name"] == "col-4"


@test
def test_revocation_is_idempotent():
    with _Tmp() as db:
        ingest_auth.enroll_collector(db, "col-5")
        ingest_auth.revoke_collector(db, "col-5")
        ingest_auth.revoke_collector(db, "col-5")


@test
def test_a_fresh_deployment_is_closed_not_open():
    with _Tmp() as db:
        assert ingest_auth.auth_mode(db) == ingest_auth.AUTH_NONE


@test
def test_an_enrolled_collector_requires_a_token():
    with _Tmp() as db:
        ingest_auth.enroll_collector(db, "col-6")
        assert ingest_auth.auth_mode(db) == ingest_auth.AUTH_REQUIRED


@test
def test_a_duplicate_name_is_refused():
    with _Tmp() as db:
        ingest_auth.enroll_collector(db, "col-7")
        try:
            ingest_auth.enroll_collector(db, "col-7")
            assert False, "duplicate enrollment must be refused"
        except ValueError as e:
            assert "already enrolled" in str(e), e


@test
def test_a_name_with_whitespace_is_refused():
    with _Tmp() as db:
        try:
            ingest_auth.enroll_collector(db, "bad name")
            assert False, "a name with whitespace must be refused"
        except ValueError as e:
            assert "whitespace" in str(e), e


@test
def test_revoking_an_unknown_collector_is_refused():
    with _Tmp() as db:
        try:
            ingest_auth.revoke_collector(db, "nobody")
            assert False, "revoking an unknown collector must be refused"
        except ValueError as e:
            assert "not currently enrolled" in str(e), e


@test
def test_the_chain_verifies_when_untouched():
    with _Tmp() as db:
        ingest_auth.enroll_collector(db, "col-8")
        ingest_auth.enroll_collector(db, "col-9")
        ingest_auth.revoke_collector(db, "col-8")
        out = ingest_auth.verify_chain(db)
        assert out["ok"] is True, out


@test
def test_the_chain_catches_a_forged_append():
    with _Tmp() as db:
        ingest_auth.enroll_collector(db, "col-10")
        import sqlite3
        con = sqlite3.connect(db)
        con.execute(
            "INSERT INTO ingest_collectors (name, token_hash, note, created_at, "
            "revoked_at, prev_hash, entry_hash) VALUES (?,?,?,?,?,?,?)",
            ("saboteur", "a" * 64, "", "2026-01-01 00:00:00", None,
             "f" * 64, "e" * 64))
        con.commit()
        con.close()
        out = ingest_auth.verify_chain(db)
        assert out["ok"] is False, out
        assert "chain break" in out["message"], out


@test
def test_update_and_delete_are_refused_by_the_database():
    with _Tmp() as db:
        ingest_auth.enroll_collector(db, "col-11")
        import sqlite3
        con = sqlite3.connect(db)
        for sql in ("UPDATE ingest_collectors SET name = 'x'",
                    "DELETE FROM ingest_collectors"):
            try:
                con.execute(sql)
                con.commit()
                assert False, "append-only trigger did not fire for: %s" % sql
            except sqlite3.IntegrityError:
                con.rollback()
        con.close()


def main():
    print(f"{len(RESULTS)} tests")
    bad = 0
    for name, ok, exc in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + name
              + ("" if ok else f" -> {exc!r}"))
        bad += 0 if ok else 1
    print(f"\n{len(RESULTS) - bad} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
