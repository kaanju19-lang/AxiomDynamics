"""Tests for ingest collector authentication."""

import os
import tempfile
from backend import ingest_auth


def test_enroll_and_resolve():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    r = ingest_auth.enroll_collector(db, "col-1")
    token = r["token"]
    resolved = ingest_auth.resolve_token(db, token)
    assert resolved["collector_name"] == "col-1"
    os.remove(db)
    os.rmdir(tmpdir)


def test_unknown_token_refused():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    try:
        ingest_auth.resolve_token(db, "unknown")
        assert False, "should have raised"
    except ValueError as e:
        assert "not recognised" in str(e)
    os.remove(db)
    os.rmdir(tmpdir)


def test_auth_mode_none_empty():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    mode = ingest_auth.auth_mode(db)
    assert mode == ingest_auth.AUTH_NONE
    os.remove(db)
    os.rmdir(tmpdir)


def test_auth_mode_required_after_enroll():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    ingest_auth.enroll_collector(db, "col-2")
    mode = ingest_auth.auth_mode(db)
    assert mode == ingest_auth.AUTH_REQUIRED
    os.remove(db)
    os.rmdir(tmpdir)


def test_revoke_collector():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    r = ingest_auth.enroll_collector(db, "col-3")
    token = r["token"]
    ingest_auth.revoke_collector(db, "col-3")
    # Token still resolves after revocation (deliberate, see module docstring)
    resolved = ingest_auth.resolve_token(db, token)
    assert resolved["collector_name"] == "col-3"
    os.remove(db)
    os.rmdir(tmpdir)


def test_revoke_idempotent():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    ingest_auth.enroll_collector(db, "col-4")
    ingest_auth.revoke_collector(db, "col-4")
    ingest_auth.revoke_collector(db, "col-4")  # must not raise
    os.remove(db)
    os.rmdir(tmpdir)


def test_chain_verify():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    ingest_auth.enroll_collector(db, "col-5")
    ingest_auth.enroll_collector(db, "col-6")
    chain = ingest_auth.verify_chain(db)
    assert chain["ok"] is True
    os.remove(db)
    os.rmdir(tmpdir)


def test_duplicate_name_refused():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    ingest_auth.enroll_collector(db, "col-7")
    try:
        ingest_auth.enroll_collector(db, "col-7")
        assert False, "should have raised"
    except ValueError as e:
        assert "already enrolled" in str(e)
    os.remove(db)
    os.rmdir(tmpdir)


def test_revoke_unknown_refused():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    try:
        ingest_auth.revoke_collector(db, "nonexistent")
        assert False, "should have raised"
    except ValueError as e:
        assert "not currently enrolled" in str(e)
    os.remove(db)
    os.rmdir(tmpdir)


def test_token_only_digest_is_stored():
    """The plaintext token must never appear in the database."""
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "t.db")
    r = ingest_auth.enroll_collector(db, "col-8")
    token = r["token"]
    with open(db, "rb") as f:
        blob = f.read()
    assert token.encode() not in blob, "plaintext token was stored"
    assert ingest_auth.token_digest(token).encode() in blob, "digest missing"
    os.remove(db)
    os.rmdir(tmpdir)


if __name__ == "__main__":
    test_enroll_and_resolve()
    test_unknown_token_refused()
    test_auth_mode_none_empty()
    test_auth_mode_required_after_enroll()
    test_revoke_collector()
    test_revoke_idempotent()
    test_chain_verify()
    test_duplicate_name_refused()
    test_revoke_unknown_refused()
    test_token_only_digest_is_stored()
    print("10 ingest_auth tests passed")
