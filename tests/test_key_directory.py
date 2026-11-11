"""Tests for the signed reviewer key directory."""

import json
import os
import tempfile

from backend import attribution, key_directory

KEY = b"\x11" * 32
OTHER_KEY = b"\x22" * 32


def _fresh():
    d = tempfile.mkdtemp()
    return os.path.join(d, "t.db")


def _register(db, reviewer, cert, key):
    return attribution.register(db, reviewer, cert, key)


def test_empty_registry_publishes_no_bindings():
    db = _fresh()
    body = key_directory.build(db)
    signed = key_directory.sign(body, KEY)
    out = key_directory.verify(signed, KEY)
    # A directory with no live binding cannot verify an attestation, and it
    # says so rather than reporting a clean pass on nothing.
    assert out["ok"] is False
    assert any(c["name"] == "live_bindings_present" and not c["ok"]
               for c in out["checks"])


def test_a_registered_reviewer_appears_with_its_binding():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    out = key_directory.verify(signed, KEY)
    assert out["ok"] is True, out
    assert out["bindings"][key_directory.key_id(b"\xaa" * 32)] == "hoffman"


def test_a_wrong_key_does_not_verify():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    out = key_directory.verify(signed, OTHER_KEY)
    assert out["ok"] is False
    assert any(c["name"] == "signature" and not c["ok"] for c in out["checks"])


def test_an_edited_binding_breaks_the_signature():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    # Relabel the reviewer in place — the attack the directory exists to catch.
    signed["entries"][0]["reviewer"] = "someone-else"
    out = key_directory.verify(signed, KEY)
    assert out["ok"] is False
    assert any(c["name"] == "signature" and not c["ok"] for c in out["checks"])


def test_an_extra_top_level_field_is_refused():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    signed["note"] = "unsigned addition"
    out = key_directory.verify(signed, KEY)
    assert out["ok"] is False
    assert any(c["name"] == "directory_no_extras" and not c["ok"]
               for c in out["checks"])


def test_a_missing_top_level_field_is_refused():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    del signed["generated_at"]
    out = key_directory.verify(signed, KEY)
    assert out["ok"] is False
    assert any(c["name"] == "directory_complete" and not c["ok"]
               for c in out["checks"])


def test_one_key_id_cannot_name_two_reviewers():
    """The relabelling attack: two names over one key. Refused by consistency."""
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    forged = dict(signed["entries"][0])
    forged["reviewer"] = "saboteur"
    signed["entries"].append(forged)
    # Re-sign so the signature passes; the directory's own consistency check
    # must still catch it, because the signer here is the attacker.
    signed = key_directory.sign(
        {"format": signed["format"], "generated_at": signed["generated_at"],
         "entries": signed["entries"]}, KEY)
    out = key_directory.verify(signed, KEY)
    assert out["ok"] is False
    assert any(c["name"] == "entries_consistent" and not c["ok"]
               for c in out["checks"])


def test_a_revoked_binding_is_not_live():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    attribution.revoke(db, "hoffman", note="left the company")
    signed = key_directory.sign(key_directory.build(db), KEY)
    out = key_directory.verify(signed, KEY)
    kid = key_directory.key_id(b"\xaa" * 32)
    assert kid not in out["bindings"], out["bindings"]
    # With no live binding left the directory must refuse to be a verifier.
    assert out["ok"] is False


def test_revocation_history_is_carried_not_hidden():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    attribution.revoke(db, "hoffman", note="left")
    body = key_directory.build(db)
    assert len(body["entries"]) == 2, body["entries"]
    assert body["entries"][0]["revoked_at"] is None
    assert body["entries"][1]["revoked_at"] is not None


def test_a_broken_registry_chain_refuses_to_build():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    # Tamper by breaking the chain with a forged INSERT: UPDATE is refused by
    # the registry's own trigger ("revocation is a new entry, not an edit"), so
    # the attack has to be an append with a wrong prev_hash.
    import sqlite3
    con = sqlite3.connect(db)
    con.execute(
        "INSERT INTO reviewer_keys (reviewer, cert_id, key_id, note, "
        "registered_at, revoked_at, prev_hash, entry_hash) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ("saboteur", "CERT-X", "0" * 16, "", "2026-01-01 00:00:00", None,
         "f" * 64, "e" * 64))
    con.commit()
    con.close()
    try:
        key_directory.build(db)
        assert False, "should have refused"
    except ValueError as e:
        assert "does not verify" in str(e)


def test_standalone_verifier_agrees_with_in_repo_verifier():
    import importlib.util
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(
        "vkd", os.path.join(here, "tools", "verify_key_directory.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)

    a = key_directory.verify(signed, KEY)
    b = mod.verify(signed, KEY)
    assert a["ok"] and b["ok"], (a, b)
    assert set(a["bindings"]) == set(b["bindings"])

    signed["entries"][0]["reviewer"] = "someone-else"
    a = key_directory.verify(signed, KEY)
    b = mod.verify(signed, KEY)
    assert a["ok"] is False and b["ok"] is False


def test_standalone_verifier_rejects_duplicate_json_keys():
    import importlib.util
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(
        "vkd2", os.path.join(here, "tools", "verify_key_directory.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    d = tempfile.mkdtemp()
    p = os.path.join(d, "dup.json")
    with open(p, "w") as f:
        f.write('{"format": "a", "format": "b"}')
    try:
        mod.load_strict(p)
        assert False, "should have refused"
    except ValueError as e:
        assert "duplicate" in str(e)


def test_sign_refuses_a_wrong_length_key():
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    body = key_directory.build(db)
    try:
        key_directory.sign(body, b"\x11" * 16)
        assert False, "should have refused"
    except ValueError as e:
        assert "32 raw bytes" in str(e)


def test_bindings_feed_the_bundle_verifier_directly():
    """
    The whole point: a recipient gets key_id -> name from the directory and
    never types a reviewer name on a command line.
    """
    db = _fresh()
    _register(db, "hoffman", "CERT-H-1", b"\xaa" * 32)
    signed = key_directory.sign(key_directory.build(db), KEY)
    out = key_directory.verify(signed, KEY)
    kid = key_directory.key_id(b"\xaa" * 32)
    assert out["bindings"][kid] == "hoffman"
