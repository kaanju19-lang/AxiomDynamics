"""Tests for the signed reviewer key directory.

The directory exists because the HMAC over an attestation does not cover the
reviewer name, so the recipient has to be told which key belongs to whom. These
tests pin the properties that make that safe to do from a file: the binding is
signed, it cannot be relabelled in place, one key cannot name two reviewers even
when the attacker signs their own directory, and a revoked binding is not live.

Run: python3 -I tests/test_key_directory.py
"""

import importlib.util
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend import attribution, key_directory  # noqa: E402

KEY = b"\x11" * 32
OTHER_KEY = b"\x22" * 32
REVIEWER_KEY = b"\xaa" * 32
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
        for name in os.listdir(self.d):
            os.remove(os.path.join(self.d, name))
        os.rmdir(self.d)
        return False


def _standalone():
    spec = importlib.util.spec_from_file_location(
        "vkd", os.path.join(ROOT, "tools", "verify_key_directory.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@test
def test_a_registered_reviewer_binds_key_to_name():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        out = key_directory.verify(signed, KEY)
        assert out["ok"] is True, out["checks"]
        assert out["bindings"][key_directory.key_id(REVIEWER_KEY)] == "hoffman"


@test
def test_a_directory_with_no_live_binding_refuses_to_pass():
    with _Tmp() as db:
        signed = key_directory.sign(key_directory.build(db), KEY)
        out = key_directory.verify(signed, KEY)
        assert out["ok"] is False, "an empty directory must not report a pass"
        assert any(c["name"] == "live_bindings_present" and not c["ok"]
                   for c in out["checks"])


@test
def test_the_wrong_key_does_not_verify():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        out = key_directory.verify(signed, OTHER_KEY)
        assert out["ok"] is False
        assert any(c["name"] == "signature" and not c["ok"] for c in out["checks"])


@test
def test_an_edited_binding_breaks_the_signature():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        signed["entries"][0]["reviewer"] = "someone-else"
        out = key_directory.verify(signed, KEY)
        assert out["ok"] is False
        assert any(c["name"] == "signature" and not c["ok"] for c in out["checks"])


@test
def test_an_extra_top_level_field_is_refused():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        signed["note"] = "unsigned addition"
        out = key_directory.verify(signed, KEY)
        assert out["ok"] is False
        assert any(c["name"] == "directory_no_extras" and not c["ok"]
                   for c in out["checks"])


@test
def test_a_missing_top_level_field_is_refused():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        del signed["generated_at"]
        out = key_directory.verify(signed, KEY)
        assert out["ok"] is False
        assert any(c["name"] == "directory_complete" and not c["ok"]
                   for c in out["checks"])


@test
def test_one_key_cannot_name_two_reviewers_even_when_resigned():
    """
    The load-bearing one. The attacker can sign their own directory, so the
    signature cannot stop this; the consistency check must.
    """
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        forged = dict(signed["entries"][0])
        forged["reviewer"] = "saboteur"
        body = {"format": signed["format"],
                "generated_at": signed["generated_at"],
                "entries": signed["entries"] + [forged]}
        resigned = key_directory.sign(body, KEY)
        out = key_directory.verify(resigned, KEY)
        assert out["ok"] is False, "a key naming two reviewers must be refused"
        assert any(c["name"] == "entries_consistent" and not c["ok"]
                   for c in out["checks"])


@test
def test_a_revoked_binding_is_not_live():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        attribution.revoke(db, "hoffman", note="left")
        signed = key_directory.sign(key_directory.build(db), KEY)
        out = key_directory.verify(signed, KEY)
        assert key_directory.key_id(REVIEWER_KEY) not in out["bindings"], out
        assert out["ok"] is False


@test
def test_revocation_history_is_carried():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        attribution.revoke(db, "hoffman", note="left")
        body = key_directory.build(db)
        assert len(body["entries"]) == 2, body["entries"]
        assert body["entries"][0]["revoked_at"] is None
        assert body["entries"][1]["revoked_at"] is not None


@test
def test_a_broken_registry_refuses_to_build():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
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
            assert False, "a broken registry chain must refuse to publish"
        except ValueError as e:
            assert "does not verify" in str(e), e


@test
def test_the_standalone_verifier_agrees_with_the_in_repo_one():
    mod = _standalone()
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        a = key_directory.verify(signed, KEY)
        b = mod.verify(signed, KEY)
        assert a["ok"] and b["ok"], (a["checks"], b["checks"])
        assert set(a["bindings"]) == set(b["bindings"])
        signed["entries"][0]["reviewer"] = "someone-else"
        assert key_directory.verify(signed, KEY)["ok"] is False
        assert mod.verify(signed, KEY)["ok"] is False


@test
def test_the_standalone_verifier_refuses_duplicate_json_keys():
    mod = _standalone()
    d = tempfile.mkdtemp()
    p = os.path.join(d, "dup.json")
    with open(p, "w") as f:
        f.write('{"format": "a", "format": "b"}')
    try:
        mod.load_strict(p)
        assert False, "a duplicate JSON key must be refused"
    except ValueError as e:
        assert "duplicate" in str(e), e
    finally:
        os.remove(p)
        os.rmdir(d)


@test
def test_signing_refuses_a_key_of_the_wrong_length():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        body = key_directory.build(db)
        try:
            key_directory.sign(body, b"\x11" * 16)
            assert False, "a 16-byte key must be refused"
        except ValueError as e:
            assert "32 raw bytes" in str(e), e


@test
def test_the_bindings_feed_the_bundle_verifier_without_a_typed_name():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        signed = key_directory.sign(key_directory.build(db), KEY)
        path = os.path.join(os.path.dirname(db), "dir.json")
        key_directory.save(signed, path)
        loaded = _standalone().load_strict(path)
        out = _standalone().verify(loaded, KEY)
        assert out["bindings"][key_directory.key_id(REVIEWER_KEY)] == "hoffman"


@test
def test_no_key_material_appears_in_the_directory():
    with _Tmp() as db:
        attribution.register(db, "hoffman", "CERT-H-1", REVIEWER_KEY)
        body = key_directory.build(db)
        blob = json.dumps(body)
        assert REVIEWER_KEY.hex() not in blob, "raw key material leaked"
        assert "token" not in blob.lower()


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
