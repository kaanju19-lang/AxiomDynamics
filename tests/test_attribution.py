"""
Tests for reviewer attribution (AD-2, the part that makes a disposition nameable).

The claim under test is narrow and must stay narrow: **a disposition row can be
bound to a registered reviewer key, and a recipient of an export can tell which
registered key attested it.** What these tests do NOT assert is that a human was
at the keyboard — nothing in software can assert that, and D09 §4.5 carries it as
a custody procedure instead.

Most tests below are attempts to make an attestation say something it should not:
move it onto another row, make it under an unregistered key, make it under
somebody else's registered key, make it after revocation, or edit it afterwards.

Run: python3 -I tests/test_attribution.py
"""

import contextlib
import hashlib
import hmac
import os
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_TMPDIR = tempfile.mkdtemp(prefix="axiom-attrib-test-")
os.environ["AXIOM_DB_PATH"] = os.path.join(_TMPDIR, "test.db")

from backend import attribution as at  # noqa: E402
from backend import ledger_export as le  # noqa: E402
from backend import store  # noqa: E402

KEY = b"\x33" * 32
HOFFMAN = b"\xa1" * 32
OKAFOR = b"\xb2" * 32


RESULTS = []


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    return fn


def fresh(n=3):
    """A ledger of n dispositions on distinct advisories.

    Every row names "Hoffman" and cert "CERT-000", because a reviewer holds one
    certificate; rows on different certificates are decisions by different
    reviewers, which is why the admissibility test below needs its own fixture.
    """
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()
    rows = []
    for i in range(n):
        rows.append(store.save_disposition(
            f"AD-2025-{i:04d}", "Hoffman", "CERT-000",
            "concur_dispatch" if i % 2 == 0 else "request_inspection",
            f"note {i}"))
    return rows


def registered_hoffman():
    """Register Hoffman on cert CERT-000, the cert every `fresh()` row carries.

    The cert must match because the verifier checks that the attestation's
    `cert_id` equals the row's — a reviewer attesting a row signed under a
    different certificate is attesting a decision they did not certify.
    """
    return at.register(store.DB_PATH, "Hoffman", "CERT-000", HOFFMAN,
                       note="chat-5 test")


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
@test
def test_a_key_id_identifies_and_does_not_reveal_the_key():
    kid = at.key_id(HOFFMAN)
    assert len(kid) == 16
    assert kid != HOFFMAN.hex()
    assert HOFFMAN.hex().startswith(kid) is False, \
        "key_id is a truncated hash, not a truncation of the key itself"


@test
def test_a_key_of_the_wrong_length_is_refused_with_a_usable_message():
    p = os.path.join(_TMPDIR, "short.key")
    with open(p, "wb") as f:
        f.write(b"\x00" * 16)
    try:
        at.load_key(p)
    except ValueError as e:
        assert "exactly 32 raw bytes" in str(e), str(e)
        assert "decode it first" in str(e), \
            "the message must tell someone with a hex file what to do about it"
    else:
        raise AssertionError("a 16-byte key was accepted")


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------
@test
def test_a_registration_lands_in_the_registry_with_a_hash_chain():
    fresh()
    e = registered_hoffman()
    assert e["reviewer"] == "Hoffman"
    assert e["key_id"] == at.key_id(HOFFMAN)
    assert e["prev_hash"] == at.REGISTRY_GENESIS, "the first entry chains from genesis"
    assert e["entry_hash"] and e["entry_hash"] != e["prev_hash"]
    v = at.verify_registry(store.DB_PATH)
    assert v["ok"], v


@test
def test_active_key_for_returns_none_once_the_key_is_revoked():
    """
    `active_key_for` is the lookup a caller uses to decide whether a reviewer can
    attest at all. If it reports the revoked registration entry as active, every
    caller that trusts it treats a withdrawn key as live — and the registry
    still verifies perfectly, so nothing else goes red.
    """
    fresh()
    registered_hoffman()
    assert at.active_key_for(store.DB_PATH, "Hoffman")["revoked_at"] is None
    at.revoke(store.DB_PATH, "Hoffman", note="compromised")
    assert at.active_key_for(store.DB_PATH, "Hoffman") is None
    assert at.active_key_for(store.DB_PATH, "Okafor") is None


@test
def test_a_second_registration_chains_to_the_first():
    fresh()
    e1 = registered_hoffman()
    e2 = at.register(store.DB_PATH, "Okafor", "CERT-002", OKAFOR)
    assert e2["prev_hash"] == e1["entry_hash"]
    assert at.verify_registry(store.DB_PATH)["ok"]


@test
def test_the_registry_cannot_be_edited_in_place():
    """A registry somebody can edit is not a register of who had which key."""
    fresh()
    registered_hoffman()
    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("UPDATE reviewer_keys SET reviewer = 'Somebody Else'")
    except sqlite3.DatabaseError as e:
        assert "append-only" in str(e), str(e)
    else:
        raise AssertionError("a registry entry was edited in place")
    finally:
        conn.close()


@test
def test_the_registry_cannot_be_deleted():
    fresh()
    registered_hoffman()
    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("DELETE FROM reviewer_keys")
    except sqlite3.DatabaseError as e:
        assert "append-only" in str(e), str(e)
    else:
        raise AssertionError("a registry entry was deleted")
    finally:
        conn.close()


@test
def test_insert_or_replace_over_a_registry_entry_is_refused():
    fresh()
    e = registered_hoffman()
    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO reviewer_keys (id, reviewer, cert_id, key_id, "
            "prev_hash, entry_hash) VALUES (?,?,?,?,?,?)",
            (e["id"], "Impostor", "CERT-999", "0" * 16, "0" * 64, "0" * 64))
    except sqlite3.DatabaseError as err:
        assert "append-only" in str(err), str(err)
    else:
        raise AssertionError("INSERT OR REPLACE overwrote a registry entry")
    finally:
        conn.close()


@test
def test_a_rewritten_prev_hash_is_caught_even_when_entry_hash_is_recomputed():
    """
    The registry chain has to check *both* directions. Editing an entry breaks
    its own `entry_hash` — but a host owner who edits `prev_hash` and then
    recomputes `entry_hash` from the edited content produces an entry whose
    self-hash is perfectly valid and whose chain link is not. Only the prev_hash
    check sees that, and without a test for it that check guards nothing.
    """
    fresh()
    registered_hoffman()
    at.register(store.DB_PATH, "Okafor", "CERT-002", OKAFOR)
    conn = sqlite3.connect(store.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("DROP TRIGGER reviewer_keys_no_update")
    forged = dict(conn.execute("SELECT * FROM reviewer_keys WHERE id = 2").fetchone())
    forged["prev_hash"] = "f" * 64
    forged["entry_hash"] = at._entry_hash(forged)
    conn.execute("UPDATE reviewer_keys SET prev_hash = ?, entry_hash = ? WHERE id = 2",
                 (forged["prev_hash"], forged["entry_hash"]))
    conn.commit()
    conn.close()
    v = at.verify_registry(store.DB_PATH)
    assert not v["ok"], "a rewritten chain link with a valid self-hash was accepted"
    assert v["broken_at_id"] == 2, v
    assert "prev_hash" in v["reason"], v["reason"]


@test
def test_verify_registry_accepts_a_freshly_built_registry():
    """The mutation-testing baseline: the chain check must not fire on good data."""
    fresh()
    registered_hoffman()
    at.register(store.DB_PATH, "Okafor", "CERT-002", OKAFOR)
    v = at.verify_registry(store.DB_PATH)
    assert v["ok"] and v["rows"] == 2, v


@test
def test_a_registration_date_cannot_be_shifted_without_breaking_the_entry_hash():
    """
    `registered_at` decides whether an attestation is admissible — it is the
    boundary the verifier compares `attested_at` against. A date outside the
    entry hash is a date anybody holding the file can move, which would let a
    key be issued today, backdated, and used to attest rows from last year.
    """
    fresh()
    registered_hoffman()
    reg = sqlite3.connect(store.DB_PATH)
    reg.row_factory = sqlite3.Row
    row = dict(reg.execute("SELECT * FROM reviewer_keys WHERE id = 1").fetchone())
    reg.execute("DROP TRIGGER reviewer_keys_no_update")
    reg.execute("UPDATE reviewer_keys SET registered_at = '2000-01-01 00:00:00' "
                "WHERE id = 1")
    reg.commit()
    reg.close()
    v = at.verify_registry(store.DB_PATH)
    assert not v["ok"], "the registration date was changed and the chain stayed valid"
    assert v["broken_at_id"] == 1, v


@test
def test_a_broken_registry_chain_is_named_by_entry_id():
    fresh()
    registered_hoffman()
    at.register(store.DB_PATH, "Okafor", "CERT-002", OKAFOR)
    # Drop the triggers to simulate a host-owner rewrite: the point of
    # verify_registry is to catch it *after* the triggers are gone.
    conn = sqlite3.connect(store.DB_PATH)
    conn.execute("DROP TRIGGER reviewer_keys_no_update")
    conn.execute("UPDATE reviewer_keys SET reviewer = 'Impostor' WHERE id = 2")
    conn.commit()
    conn.close()
    v = at.verify_registry(store.DB_PATH)
    assert not v["ok"]
    assert v["broken_at_id"] == 2, v
    assert "entry_hash does not match its content" in v["reason"], v


# ---------------------------------------------------------------------------
# Attestation
# ---------------------------------------------------------------------------
@test
def test_attesting_a_row_records_a_value_over_its_record_hash():
    rows = fresh()
    registered_hoffman()
    a = at.attest(store.DB_PATH, rows[1]["id"], HOFFMAN)
    assert a["key_id"] == at.key_id(HOFFMAN)
    want = hmac.new(HOFFMAN, ("axiom-attestation/v1:%s" % rows[1]["record_hash"])
                    .encode("utf-8"), hashlib.sha256).hexdigest()
    assert a["value"] == want


@test
def test_an_unregistered_key_attests_nothing():
    """Without this refusal the attestation is a signature by anybody about anything."""
    rows = fresh()
    try:
        at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    except ValueError as e:
        assert "not in the reviewer registry" in str(e), str(e)
    else:
        raise AssertionError("an unregistered key produced an attestation")
    assert at.attestations(store.DB_PATH) == {}


@test
def test_a_reviewer_cannot_attest_another_reviewers_row():
    rows = fresh()
    registered_hoffman()
    at.register(store.DB_PATH, "Okafor", "CERT-002", OKAFOR)
    try:
        # Row 0 names "Hoffman"; Okafor's key is registered and live.
        at.attest(store.DB_PATH, rows[0]["id"], OKAFOR)
    except ValueError as e:
        assert "is not an attestation" in str(e), str(e)
    else:
        raise AssertionError("Okafor attested Hoffman's decision")
    assert at.attestations(store.DB_PATH) == {}


@test
def test_a_reviewer_cannot_attest_a_row_recorded_under_another_certificate():
    """
    The verifier already rejected this; `attest` used to write it anyway. A
    control that records what no checker will accept makes a bundle that fails
    for the recipient and passes on the machine that produced it.
    """
    fresh()
    other = store.save_disposition("AD-2025-9000", "Hoffman", "CERT-777",
                                   "concur_dispatch", "recorded under another cert")
    registered_hoffman()
    try:
        at.attest(store.DB_PATH, other["id"], HOFFMAN)
    except ValueError as e:
        assert "recorded under cert CERT-777" in str(e), str(e)
    else:
        raise AssertionError("a key attested a row recorded under a different cert")
    assert at.attestations(store.DB_PATH) == {}


@test
def test_a_revoked_key_cannot_attest_new_rows():
    rows = fresh()
    registered_hoffman()
    at.revoke(store.DB_PATH, "Hoffman", note="custody transferred")
    try:
        at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    except ValueError as e:
        assert "revoked at" in str(e), str(e)
    else:
        raise AssertionError("a revoked key produced a new attestation")


@test
def test_an_attestation_made_before_revocation_is_still_valid():
    """
    Revocation stops new attestations; it does not retroactively unmake what the
    key attested while it was live. Anything else would let a revocation erase
    history, which is the whole failure the ledger exists to prevent.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    at.revoke(store.DB_PATH, "Hoffman", note="left the company")
    v = at.verify_attestations(store.DB_PATH)
    assert v["ok"], v["bad"]
    assert v["attested"] == 1


@test
def test_an_attestation_cannot_be_edited_or_deleted():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    for statement in ("UPDATE attestations SET value = 'x'",
                      "DELETE FROM attestations"):
        conn = sqlite3.connect(store.DB_PATH)
        try:
            conn.execute(statement)
        except sqlite3.DatabaseError as e:
            assert "attestation" in str(e), str(e)
        else:
            raise AssertionError("%r was permitted" % statement)
        finally:
            conn.close()


@test
def test_insert_or_replace_over_an_attestation_is_refused():
    """
    `BEGIN OR REPLACE` deletes and re-inserts, and SQLite does not fire the
    delete trigger for it unless recursive_triggers is on. Without the replace
    guard, an attestation can be swapped in place while every other trigger
    reads as present — which is the state the design would have shipped in had
    this test not been written.
    """
    rows = fresh()
    registered_hoffman()
    a = at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO attestations (row_id, key_id, value) "
            "VALUES (?,?,?)", (rows[0]["id"], "0" * 16, "forged"))
    except sqlite3.DatabaseError as e:
        assert "recorded once" in str(e), str(e)
    else:
        raise AssertionError("INSERT OR REPLACE overwrote an attestation")
    finally:
        conn.close()
    assert at.attestations(store.DB_PATH)[rows[0]["id"]]["value"] == a["value"]


@test
def test_verify_attestations_names_the_row_it_could_not_explain():
    """"3 of 40 failed" is not actionable; "row 17 failed" is."""
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    at.attest(store.DB_PATH, rows[1]["id"], HOFFMAN)
    # Rewrite a row behind the attestation. A host owner can do that after
    # dropping the ledger's own triggers — which is exactly the attack
    # verify_attestations exists to make visible after the fact.
    conn = sqlite3.connect(store.DB_PATH)
    conn.execute("DROP TRIGGER IF EXISTS dispositions_no_update")
    conn.execute("UPDATE dispositions SET reviewer_name = 'Okafor' WHERE id = ?",
                 (rows[1]["id"],))
    conn.commit()
    conn.close()
    v = at.verify_attestations(store.DB_PATH)
    assert not v["ok"], v
    ids = [b["row_id"] for b in v["bad"]]
    assert rows[1]["id"] in ids, v["bad"]
    assert rows[0]["id"] not in ids, \
        "the untouched row must not be reported: %r" % (v["bad"],)


@test
def test_the_attestations_are_written_where_they_do_not_change_the_row_hash():
    """Storage is beside the ledger, not inside it. record_hash must not move."""
    rows = fresh()
    before = [r["record_hash"] for r in store.disposition_history("AD-2025-0000")]
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    after = [r["record_hash"] for r in store.disposition_history("AD-2025-0000")]
    assert before == after, "attesting a row changed its record_hash"


# ---------------------------------------------------------------------------
# What reaches the recipient
# ---------------------------------------------------------------------------
@test
def test_the_export_carries_the_attestation_inside_each_record():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[1]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    rec = [r for r in b["records"] if r["id"] == rows[1]["id"]][0]
    assert rec["attribution"]["reviewer"] == "Hoffman"
    assert rec["attribution"]["cert_id"] == "CERT-000"
    assert rec["attribution"]["key_id"] == at.key_id(HOFFMAN)
    assert b["manifest"]["attributed_records"] == 1
    assert b["manifest"]["attribution_available"] is True


@test
def test_the_bundle_top_level_stays_exactly_the_four_signed_parts():
    """
    Attribution travels inside `records` deliberately. A top-level attribution
    block would fail `bundle_no_extras` in every verifier and would have to be
    let through by loosening that check — a security regression in exchange for
    tidiness.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    assert set(b) == {"format", "manifest", "records", "signature"}, sorted(b)


@test
def test_a_bundle_with_attribution_still_verifies_with_and_without_the_key():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    r = le.verify_bundle(b, KEY)
    assert r["ok"], r["checks"]
    assert "attestations_verified" not in {c["name"] for c in r["checks"]}, \
        "without keys supplied, the cryptographic check must not claim to have run"
    r2 = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
    assert r2["ok"], r2["checks"]
    verified = [c for c in r2["checks"] if c["name"] == "attestations_verified"]
    assert verified and verified[0]["ok"], "the key-carrying run must report the check"


@test
def test_an_attestation_moved_onto_another_row_fails_verification():
    """
    The attack the design must survive: take a real attestation and put it on a
    row the reviewer did not sign. The record_hash differs, so the HMAC differs.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    src = [r for r in b["records"] if r["id"] == rows[0]["id"]][0]
    dst = [r for r in b["records"] if r["id"] == rows[1]["id"]][0]
    dst["attribution"] = dict(src["attribution"])
    r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
    assert not r["ok"], "a lifted attestation verified"
    assert "attribution_consistent" in set(r["failed"]), r["failed"]


@test
def test_an_attestation_whose_cert_id_was_swapped_fails_verification():
    """
    `attest()` refuses to write a cert mismatch, so this mutation can only come
    from editing the bundle. It still has to be caught: the `cert_id` travelling
    in the attribution is the reviewer's authority to have made this decision,
    and substituting it changes who is claimed to have certified the row.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    b["records"][0]["attribution"]["cert_id"] = "CERT-999"
    r = le.verify_bundle(b, KEY)
    assert "attribution_consistent" in set(r["failed"]), r["failed"]


@test
def test_supplying_a_key_that_matches_nothing_is_reported_not_ignored():
    """
    The distinction a verifier has to preserve: *checked and passed* is not the
    same as *could not check*. If the caller supplied a key, every attributed
    record must have been checked against one, and a record naming a key the
    caller did not supply is a check that did not happen.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(OKAFOR): (OKAFOR, "Okafor")})
    assert "attestations_verified" in set(r["failed"]), \
        "a key that matches no record was silently accepted"


@test
def test_an_attestation_that_names_a_different_reviewer_than_the_row_fails():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    b["records"][0]["attribution"]["reviewer"] = "Okafor"
    r = le.verify_bundle(b, KEY)
    assert "attribution_consistent" in set(r["failed"]), r["failed"]


@test
def test_the_standalone_verifier_reports_a_key_that_matches_nothing():
    """The same distinction, in the file the recipient actually runs."""
    import json
    import subprocess
    d = tempfile.mkdtemp(prefix="axiom-attrib-unmatched-")
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    bp, kp = os.path.join(d, "b.json"), os.path.join(d, "k.bin")
    rk = os.path.join(d, "okafor.key")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(b, f)
    with open(kp, "wb") as f:
        f.write(KEY)
    with open(rk, "wb") as f:
        f.write(OKAFOR)
    out = subprocess.run(
        [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--bundle", bp, "--key-file", kp, "--json",
         "--reviewer-key", "%s=%s" % (at.key_id(OKAFOR), rk)],
        capture_output=True, text=True, cwd=d)
    result = json.loads(out.stdout)
    assert out.returncode == 1, result
    assert "attestations_verified" in result["failed"], result["failed"]


@test
def test_an_attestation_that_predates_its_keys_registration_fails():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    a = b["records"][0]["attribution"]
    a["registered_at"] = "2099-01-01 00:00:00"
    r = le.verify_bundle(b, KEY)
    assert "attribution_consistent" in set(r["failed"]), r["failed"]


@test
def test_a_row_recorded_after_its_keys_revocation_fails():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    at.revoke(store.DB_PATH, "Hoffman")
    b = le.build_bundle(KEY)
    a = b["records"][0]["attribution"]
    a["revoked_at"] = "2000-01-01 00:00:00"
    r = le.verify_bundle(b, KEY)
    assert "attribution_consistent" in set(r["failed"]), r["failed"]


@test
def test_the_manifest_cannot_overstate_or_understate_how_many_rows_are_attested():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    b["manifest"]["attributed_records"] = 3
    assert "attribution_count" in set(le.verify_bundle(b, KEY)["failed"])
    b = le.build_bundle(KEY)
    b["manifest"]["attribution_available"] = False
    assert "attribution_claim" in set(le.verify_bundle(b, KEY)["failed"])


@test
def test_a_revoked_key_cannot_be_re_registered_back_into_use():
    """
    Re-registering the same key bytes after a revocation is not a renewal; it is
    the same secret, and whatever made it untrustworthy is still true. Without
    this refusal a revocation could be undone by appending an entry, which makes
    the whole revocation concept optional.
    """
    rows = fresh()
    registered_hoffman()
    at.revoke(store.DB_PATH, "Hoffman", note="compromised")
    try:
        at.register(store.DB_PATH, "Hoffman", "CERT-000", HOFFMAN, note="second try")
    except ValueError as e:
        assert "revoked" in str(e), str(e)
    else:
        raise AssertionError("a revoked key was registered back into use")
    # And the refusal is what stops the use, not luck: nothing got written.
    assert [e["revoked_at"] is None for e in at.registry(store.DB_PATH)] == [True, False]
    try:
        at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    except ValueError as e:
        assert "revoked" in str(e), str(e)
    else:
        raise AssertionError("a revoked key attested a row")
    assert at.attestations(store.DB_PATH) == {}


@test
def test_one_key_cannot_be_registered_to_a_second_reviewer():
    """
    A key shared between two reviewers destroys the only thing an attestation
    says. Before this check `register` refused only a *revoked* key, so a
    second registration with the same bytes under a different name succeeded —
    and because `attest` resolves the newest entry for a key_id, the second
    reviewer could then attest rows naming themselves, while the original
    reviewer was locked out of their own key.

    The register is append-only, so a bad binding can never be removed. The key
    directory caught the conflict at publish time, which is far too late. This
    asserts the write is refused instead.
    """
    fresh()
    at.register(store.DB_PATH, "Hoffman", "CERT-000", HOFFMAN)
    try:
        at.register(store.DB_PATH, "Okafor", "CERT-002", HOFFMAN)
    except ValueError as exc:
        assert "already bound" in str(exc), exc
    else:
        raise AssertionError("a second reviewer was allowed to take a live key")
    # The original binding still governs: Hoffman can still attest with it.
    row = store.save_disposition("AD-2025-8888", "Hoffman", "CERT-000",
                                 "concur_dispatch", "")
    at.attest(store.DB_PATH, row["id"], HOFFMAN)


@test
def test_a_renewal_under_a_new_certificate_is_still_allowed_for_the_same_key():
    """
    The counterpart to the refusal above, and the reason it is narrower than it
    first looks. Renewing is registering the same key under a new certificate
    for the *same* reviewer — the test below depends on it, and so does the
    rotation procedure in D09 §8.4.5. The refusal must be about the reviewer
    changing, never about the certificate.
    """
    fresh()
    at.register(store.DB_PATH, "Hoffman", "CERT-OLD", HOFFMAN, note="original")
    at.register(store.DB_PATH, "Hoffman", "CERT-NEW", HOFFMAN, note="renewed")
    rows = [r for r in at.registry(store.DB_PATH) if r["reviewer"] == "Hoffman"]
    assert len(rows) == 2, rows
    assert rows[-1]["cert_id"] == "CERT-NEW", rows[-1]


@test
def test_a_renewal_under_a_new_certificate_exports_the_new_certificate():
    """The renewal case end to end: attest after the renewal, export the renewal.

    A test that only checks the *first* registration would still pass with the
    export taking the oldest entry, because the oldest and newest agree until a
    renewal happens."""
    fresh()
    at.register(store.DB_PATH, "Hoffman", "CERT-OLD", HOFFMAN, note="original")
    e2 = at.register(store.DB_PATH, "Hoffman", "CERT-NEW", HOFFMAN, note="renewed")
    row = store.save_disposition("AD-2025-7777", "Hoffman", "CERT-NEW",
                                 "concur_dispatch", "under the renewed cert")
    at.attest(store.DB_PATH, row["id"], HOFFMAN)
    a = at.attribution_for_export(store.DB_PATH)[row["id"]]
    assert a["cert_id"] == "CERT-NEW", \
        "export reported the superseded certificate %r" % a["cert_id"]
    assert a["registered_at"] == e2["registered_at"]
    b = le.build_bundle(KEY)
    r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
    assert r["ok"], r["checks"]


@test
def test_the_export_reports_the_registration_entry_not_the_revocation_entry():
    """
    Directly on `attribution_for_export`, because this is a function-level
    decision and a bundle-level test cannot see the difference when the two
    timestamps land in the same second — which, on a fast test box, they do.

    A revoked key has two registry entries. Picking the last one says the key
    was registered at the moment it was revoked; picking the first real entry
    says what actually happened. Both produce a bundle whose HMAC verifies, so
    only a test at this level pins the behaviour.
    """
    fresh()
    e1 = registered_hoffman()
    at.attest(store.DB_PATH, 1, HOFFMAN)
    e2 = at.revoke(store.DB_PATH, "Hoffman", note="left")
    assert e2["id"] != e1["id"], "revocation must be a new entry, not an edit"
    rev = [e for e in at.registry(store.DB_PATH) if e["id"] == e2["id"]][0]
    a = at.attribution_for_export(store.DB_PATH)[1]
    assert a["registered_at"] == e1["registered_at"], \
        "registered_at came from the revocation entry, not the registration"
    assert a["revoked_at"] == rev["revoked_at"]
    assert a["registered_at"] != rev["registered_at"] or \
        a["registered_at"] == e1["registered_at"], "registration must come from entry 1"
    # And the invariant the verifier enforces must hold on honest data.
    assert a["registered_at"] <= a["attested_at"] <= a["revoked_at"], a


@test
def test_an_attestation_by_a_key_with_no_registration_is_omitted_not_invented():
    """A registration cannot be deleted through the API, but a host owner who
    dropped the trigger can delete one. The export must then leave the record
    unattributed rather than carry a registration time it made up."""
    fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, 1, HOFFMAN)
    conn = sqlite3.connect(store.DB_PATH)
    conn.execute("DROP TRIGGER reviewer_keys_no_delete")
    conn.execute("DELETE FROM reviewer_keys")
    conn.commit()
    conn.close()
    assert at.attribution_for_export(store.DB_PATH) == {}
    v = at.verify_attestations(store.DB_PATH)
    assert not v["ok"], "an attestation with no registration entry must be reported"


@test
def test_verify_attestations_flags_a_row_recorded_after_its_key_was_revoked():
    """
    `attest()` refuses this at write time, so reaching it means somebody got the
    row in behind the guard — dropped a trigger, or restored a row. The registry
    has two entries for a revoked key and `verify_attestations` has to consult
    the *registration* one; if it picks the newest entry instead it reads
    `revoked_at` from the registration (which is null) and this check can never
    fire. That is the difference between a control and a function that returns ok.
    """
    fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, 1, HOFFMAN)
    at.revoke(store.DB_PATH, "Hoffman", note="left")
    conn = sqlite3.connect(store.DB_PATH)
    conn.execute("DROP TRIGGER dispositions_no_update")
    conn.execute("UPDATE dispositions SET recorded_at = '2099-01-01 00:00:00' "
                 "WHERE id = 1")
    conn.commit()
    conn.close()
    v = at.verify_attestations(store.DB_PATH)
    assert not v["ok"], "a row postdating its key's revocation was accepted"
    assert any("revoked" in b["reason"] for b in v["bad"]), v["bad"]


@test
def test_verify_attestations_accepts_an_honest_post_revocation_state():
    """The baseline for the check above: revocation alone must not fail anything."""
    fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, 1, HOFFMAN)
    at.revoke(store.DB_PATH, "Hoffman", note="left")
    v = at.verify_attestations(store.DB_PATH)
    assert v["ok"], v["bad"]


@test
def test_a_revoked_key_still_exports_its_pre_revocation_attestation_correctly():
    """
    The registration time must be the registration, not the revocation that
    followed it. Reporting the revocation entry's timestamp says the key was
    registered when it was revoked, and every honest attestation made before
    then fails the ordering check — the check firing on innocent data.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    at.revoke(store.DB_PATH, "Hoffman", note="left")
    b = le.build_bundle(KEY)
    a = b["records"][0]["attribution"]
    assert a["registered_at"] <= a["attested_at"], (a["registered_at"], a["attested_at"])
    assert a["revoked_at"] is not None, "the revocation must travel with the record"
    assert a["revoked_at"] >= a["attested_at"]
    r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
    assert r["ok"], r["checks"]


@test
def test_a_record_with_no_attestation_is_not_a_failure():
    """An unattested decision is an honest state, and the count says how many."""
    fresh()
    b = le.build_bundle(KEY)
    r = le.verify_bundle(b, KEY)
    assert r["ok"], r["checks"]
    assert b["manifest"]["attributed_records"] == 0


# ---------------------------------------------------------------------------
# The standalone verifier must agree, and must not need our code
# ---------------------------------------------------------------------------
def _run_standalone(bundle, key, reviewer_key=None):
    """Run the recipient-facing verifier on a bundle and return (code, result).

    `reviewer_key` is (key_id, reviewer_name_or_None, key_bytes) or None. The
    reviewer name is what lets the verifier catch a key holder relabelling their
    own attestation, so tests that care about that must pass it.
    """
    import json
    import subprocess
    d = tempfile.mkdtemp(prefix="axiom-attrib-sa-")
    bp, kp = os.path.join(d, "b.json"), os.path.join(d, "k.bin")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(bundle, f)
    with open(kp, "wb") as f:
        f.write(key)
    cmd = [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
           "--bundle", bp, "--key-file", kp, "--json"]
    if reviewer_key is not None:
        kid, name, rk = reviewer_key
        rp = os.path.join(d, "reviewer.key")
        with open(rp, "wb") as f:
            f.write(rk)
        spec = "%s=%s:%s" % (kid, name, rp) if name else "%s=%s" % (kid, rp)
        cmd += ["--reviewer-key", spec]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=d)
    return out.returncode, (json.loads(out.stdout) if out.stdout.strip()
                            else {"stderr": out.stderr})


def _attested_bundle():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    return le.build_bundle(KEY)


@test
def test_the_standalone_verifier_and_the_backend_agree_on_every_attribution_tamper():
    """
    The parity test. Every structural tamper below must be caught by *both*
    verifiers. A check that only the exporter's copy has is a check the
    recipient cannot run, and the two disagreeing means a bundle passes here and
    fails at the regulator — the worst outcome for a verification story.
    """
    cases = {
        "reviewer swapped": lambda b: b["records"][0]["attribution"].__setitem__(
            "reviewer", "Okafor"),
        "cert swapped": lambda b: b["records"][0]["attribution"].__setitem__(
            "cert_id", "CERT-999"),
        "predates registration": lambda b: b["records"][0]["attribution"].__setitem__(
            "registered_at", "2099-01-01 00:00:00"),
        "count overstated": lambda b: b["manifest"].__setitem__(
            "attributed_records", 7),
        "available contradicted": lambda b: b["manifest"].__setitem__(
            "attribution_available", False),
        "ordering field removed": lambda b: b["records"][0]["attribution"].pop(
            "registered_at"),
        "revoked after the row": lambda b: b["records"][0]["attribution"].__setitem__(
            "revoked_at", "2000-01-01 00:00:00"),
    }
    for label, tamper in cases.items():
        b = _attested_bundle()
        tamper(b)
        # Re-sign after tampering. Without this the bundle fails on `signature`
        # and both verifiers agree for the wrong reason — the structural
        # attribution check is never what catches anything, and a mutation
        # disabling it would survive. This models the attacker who holds the
        # export key, which is the only attacker the structural checks are for:
        # anyone else is stopped by the signature.
        b = le.sign(b, KEY)  # sign() returns a copy; it does not mutate
        back = le.verify_bundle(b, KEY)
        code, sa = _run_standalone(b, KEY)
        assert not back["ok"], "%s: backend accepted it" % label
        assert code == 1 and not sa["ok"], "%s: standalone accepted it: %r" % (label, sa)
        assert "signature" not in set(back["failed"]), \
            "%s: caught by the signature, so the test proves nothing" % label
        both = set(back["failed"]) & set(sa["failed"])
        assert both, ("%s: the two verifiers failed on different checks — "
                      "backend %r, standalone %r"
                      % (label, back["failed"], sa["failed"]))


@test
def test_the_standalone_verifier_accepts_an_honest_attested_bundle_with_the_key():
    b = _attested_bundle()
    code, sa = _run_standalone(b, KEY, (at.key_id(HOFFMAN), "Hoffman", HOFFMAN))
    assert code == 0, sa
    verified = [c for c in sa["checks"] if c["name"] == "attestations_verified"]
    assert verified and verified[0]["ok"], sa["checks"]


@test
def test_the_standalone_verifier_sees_attribution_and_still_needs_no_database():
    import json
    import subprocess
    d = tempfile.mkdtemp(prefix="axiom-attrib-standalone-")
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    bp, kp = os.path.join(d, "b.json"), os.path.join(d, "k.bin")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(b, f)
    with open(kp, "wb") as f:
        f.write(KEY)
    out = subprocess.run(
        [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--bundle", bp, "--key-file", kp, "--json"],
        capture_output=True, text=True, cwd=d)
    result = json.loads(out.stdout)
    assert out.returncode == 0, result
    names = {c["name"] for c in result["checks"]}
    assert "attribution_consistent" in names, sorted(names)
    assert "attestations_verified" not in names, \
        "without --reviewer-key the standalone verifier must not claim to have checked"


@test
def test_the_standalone_verifier_recomputes_with_a_reviewer_key():
    import json
    import subprocess
    d = tempfile.mkdtemp(prefix="axiom-attrib-standalone-key-")
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    bp, kp = os.path.join(d, "b.json"), os.path.join(d, "k.bin")
    rk = os.path.join(d, "hoffman.key")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(b, f)
    with open(kp, "wb") as f:
        f.write(KEY)
    with open(rk, "wb") as f:
        f.write(HOFFMAN)
    out = subprocess.run(
        [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--bundle", bp, "--key-file", kp, "--json",
         "--reviewer-key", "%s=%s" % (at.key_id(HOFFMAN), rk)],
        capture_output=True, text=True, cwd=d)
    result = json.loads(out.stdout)
    assert out.returncode == 0, result
    verified = [c for c in result["checks"] if c["name"] == "attestations_verified"]
    assert verified and verified[0]["ok"], result["checks"]


@test
def test_a_flipped_attestation_value_fails_in_both_verifiers():
    """
    Every structural field can be right — right reviewer, right cert, plausible
    timestamps — and the value itself still have to recompute. That is the only
    check that requires the key, and therefore the only one that cannot be
    satisfied by editing the bundle consistently.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    real = b["records"][0]["attribution"]["attestation"]
    b["records"][0]["attribution"]["attestation"] = ("f" if real[0] != "f" else "0") + real[1:]
    r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
    assert "attribution_consistent" in set(r["failed"]), r["failed"]
    # Without the key it must NOT be reported as a failure — the verifier cannot
    # know. It must also not be reported as verified.
    r2 = le.verify_bundle(b, KEY)
    assert "attestations_verified" not in {c["name"] for c in r2["checks"]}


@test
def test_the_standalone_verifier_catches_a_flipped_attestation_value():
    import json
    import subprocess
    d = tempfile.mkdtemp(prefix="axiom-attrib-flip-")
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    real = b["records"][0]["attribution"]["attestation"]
    b["records"][0]["attribution"]["attestation"] = ("f" if real[0] != "f" else "0") + real[1:]
    bp, kp = os.path.join(d, "b.json"), os.path.join(d, "k.bin")
    rk = os.path.join(d, "hoffman.key")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(b, f)
    with open(kp, "wb") as f:
        f.write(KEY)
    with open(rk, "wb") as f:
        f.write(HOFFMAN)
    out = subprocess.run(
        [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--bundle", bp, "--key-file", kp, "--json",
         "--reviewer-key", "%s=%s" % (at.key_id(HOFFMAN), rk)],
        capture_output=True, text=True, cwd=d)
    result = json.loads(out.stdout)
    assert out.returncode == 1, result
    assert "attribution_consistent" in result["failed"], result["failed"]


@test
def test_the_standalone_verifier_rejects_a_mislabelled_reviewer_key():
    """A key that does not hash to its label is not that key; say so plainly
    rather than reporting every attestation as forged."""
    import json
    import subprocess
    d = tempfile.mkdtemp(prefix="axiom-attrib-mislabel-")
    fresh()
    registered_hoffman()
    b = le.build_bundle(KEY)
    bp, kp = os.path.join(d, "b.json"), os.path.join(d, "k.bin")
    rk = os.path.join(d, "wrong.key")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(b, f)
    with open(kp, "wb") as f:
        f.write(KEY)
    with open(rk, "wb") as f:
        f.write(OKAFOR)
    out = subprocess.run(
        [sys.executable, "-I", "-B", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--bundle", bp, "--key-file", kp,
         "--reviewer-key", "%s=%s" % (at.key_id(HOFFMAN), rk)],
        capture_output=True, text=True, cwd=d)
    assert out.returncode == 2, (out.returncode, out.stdout, out.stderr)
    assert "is not the key labelled" in out.stderr, out.stderr


# ---------------------------------------------------------------------------
# Findings from the adversarial audit, 2026-11-11
# ---------------------------------------------------------------------------
@test
def test_a_key_holder_cannot_relabel_their_own_attestation_with_anothers_name():
    """
    Audit finding 1, the serious one. The HMAC covers `record_hash` only, so the
    `reviewer` field in the block is not itself attested. A holder of *any*
    registered reviewer key could therefore take a row naming somebody else,
    compute a valid attestation with their own key, label the block with the
    other reviewer's name, re-sign the bundle — and both verifiers returned
    ok=True. The claim "an attestation cannot be attributed to a reviewer who did
    not make it" was false at the identity level, which is the only level that
    matters.

    The fix is that the verifier is told which reviewer each key belongs to. The
    bundle cannot be trusted to say who its own key belongs to.
    """
    fresh()
    at.register(store.DB_PATH, "Okafor", "CERT-000", OKAFOR)
    b = le.build_bundle(KEY)
    r = b["records"][0]
    val = hmac.new(OKAFOR, ("axiom-attestation/v1:" + r["record_hash"]).encode(),
                   hashlib.sha256).hexdigest()
    r["attribution"] = {
        "reviewer": "Hoffman",           # the row names Hoffman, so this passes
        "cert_id": "CERT-000",           # as does this
        "key_id": at.key_id(OKAFOR),     # but the key is Okafor's
        "attestation": val,              # and the HMAC genuinely recomputes
        "attested_at": "2026-01-01 00:00:00",
        "registered_at": "2026-01-01 00:00:00",
        "revoked_at": None,
    }
    b["manifest"]["attributed_records"] = 1
    b["manifest"]["attribution_available"] = True
    b = le.sign(b, KEY)
    r2 = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(OKAFOR): (OKAFOR, "Okafor")})
    assert not r2["ok"], "a key holder relabelled their attestation as another reviewer"
    assert "attribution_consistent" in set(r2["failed"]), r2["failed"]
    code, sa = _run_standalone(b, KEY, (at.key_id(OKAFOR), "Okafor", OKAFOR))
    assert code == 1 and not sa["ok"], "the standalone verifier accepted the relabelled block"


@test
def test_the_same_relabelling_passes_when_the_verifier_is_told_nothing():
    """
    The disclosed limit, asserted rather than assumed: a verifier given a key
    with no reviewer name still recomputes the HMAC but cannot catch relabelling.
    That is why the CLI warns when a name is omitted.
    """
    fresh()
    at.register(store.DB_PATH, "Okafor", "CERT-000", OKAFOR)
    b = le.build_bundle(KEY)
    r = b["records"][0]
    val = hmac.new(OKAFOR, ("axiom-attestation/v1:" + r["record_hash"]).encode(),
                   hashlib.sha256).hexdigest()
    r["attribution"] = {
        "reviewer": "Hoffman", "cert_id": "CERT-000",
        "key_id": at.key_id(OKAFOR), "attestation": val,
        "attested_at": "2026-01-01 00:00:00",
        "registered_at": "2026-01-01 00:00:00", "revoked_at": None,
    }
    b["manifest"]["attributed_records"] = 1
    b["manifest"]["attribution_available"] = True
    b = le.sign(b, KEY)
    r2 = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(OKAFOR): (OKAFOR, None)})
    assert r2["ok"], ("an unnamed key caught relabelling it should not be able to "
                      "catch — if this now fails, the limit moved and the docs "
                      "need updating")


@test
def test_deleting_an_ordering_field_does_not_disable_the_ordering_check():
    """
    Audit finding 2. Every ordering comparison was guarded by truthiness, so
    popping `registered_at` or `revoked_at` from the block silently skipped the
    check. A backdated attestation failed correctly and then passed once its
    `registered_at` was removed. Required fields are now required.
    """
    for field in ("registered_at", "attested_at", "revoked_at", "attestation",
                  "key_id", "reviewer", "cert_id"):
        rows = fresh()
        registered_hoffman()
        at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
        b = le.build_bundle(KEY)
        del b["records"][0]["attribution"][field]
        b = le.sign(b, KEY)
        r = le.verify_bundle(b, KEY)
        assert "attribution_consistent" in set(r["failed"]), \
            "removing %r disabled a check instead of failing" % field
        code, sa = _run_standalone(b, KEY)
        assert code == 1, "the standalone verifier accepted a block missing %r" % field


@test
def test_a_backdated_attestation_stays_caught_even_after_the_field_is_removed():
    """The specific exploit: registered_at in the future fails, and deleting it
    must not turn that failure into a pass."""
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    b["records"][0]["attribution"]["registered_at"] = "2099-01-01 00:00:00"
    assert "attribution_consistent" in set(le.verify_bundle(b, KEY)["failed"])
    del b["records"][0]["attribution"]["registered_at"]
    b = le.sign(b, KEY)
    assert "attribution_consistent" in set(le.verify_bundle(b, KEY)["failed"])


@test
def test_a_fabricated_attribution_is_not_indistinguishable_from_an_honest_one():
    """
    Audit finding 3. With no reviewer key, a fabricated block carrying 32 zero
    bytes used to verify clean — a keyless recipient could not tell a fabricated
    attestation from an honest one. That is inherent to HMAC without the key and
    is disclosed, but the count and the claim are still checkable, and the
    disclosure must say plainly that a keyless recipient cannot distinguish them.
    """
    fresh()
    b = le.build_bundle(KEY)
    r = b["records"][0]
    r["attribution"] = {
        "reviewer": "Hoffman", "cert_id": "CERT-000", "key_id": "0" * 16,
        "attestation": "0" * 64,
        "attested_at": "2026-01-01 00:00:00",
        "registered_at": "2026-01-01 00:00:00", "revoked_at": None,
    }
    b["manifest"]["attributed_records"] = 0   # the honest count for the rest
    b = le.sign(b, KEY)
    r2 = le.verify_bundle(b, KEY)
    # The count is wrong, so this is caught; but the structural checks pass, and
    # that limit is what the docs must state.
    assert "attribution_count" in set(r2["failed"])
    b = le.build_bundle(KEY)
    b["records"][0]["attribution"] = r["attribution"]
    b["manifest"]["attributed_records"] = 1
    b["manifest"]["attribution_available"] = True
    b = le.sign(b, KEY)
    keyless = le.verify_bundle(b, KEY)
    assert keyless["ok"], ("a keyless recipient now catches this, which would "
                           "mean the disclosed limit is wrong in the safe direction "
                           "— update the docs")
    with_key = le.verify_bundle(b, KEY, reviewer_keys={"0" * 16: (HOFFMAN, None)})
    assert "attribution_consistent" in set(with_key["failed"]), \
        "the key-carrying run must catch a fabricated attestation"


@test
def test_a_revocation_landing_between_the_check_and_the_write_is_refused():
    """
    Audit finding 4. `attest()` read the registry on one connection and wrote on
    another, so a revoke() in between produced an attestation recorded after the
    revocation. The refusal is now re-evaluated under the write lock.
    """
    rows = fresh()
    registered_hoffman()
    original = at._atomic

    class _Hook:
        """A `_atomic` that revokes the key exactly once, just before the write."""
        fired = False

    @contextlib.contextmanager
    def hooked(db_path):
        if not _Hook.fired:
            _Hook.fired = True
            at.revoke(db_path, "Hoffman", note="raced")
        with original(db_path) as conn:
            yield conn

    try:
        at._atomic = hooked
        try:
            at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
        except ValueError as e:
            assert "revoked" in str(e), str(e)
        else:
            raise AssertionError("an attestation was written after the key was revoked")
    finally:
        at._atomic = original
    assert at.attestations(store.DB_PATH) == {}


@test
def test_a_certificate_renewal_does_not_break_an_honest_export():
    """
    Audit finding 5. `attest` took the newest registry entry and the export took
    the first, so after a renewal an honest attestation exported under the
    superseded certificate and failed the verifier's cert check — a bundle that
    fails at the recipient and passes here.
    """
    fresh()
    e1 = registered_hoffman()                        # CERT-000
    # Renew the same key under a new certificate, as a cert renewal would.
    e2 = at.register(store.DB_PATH, "Hoffman", "CERT-000", HOFFMAN,
                     note="renewal")                  # same cert, new entry
    rows = store.disposition_history("AD-2025-0000")
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    exported = at.attribution_for_export(store.DB_PATH)[rows[0]["id"]]
    assert exported["cert_id"] == "CERT-000"
    assert exported["registered_at"] == e2["registered_at"], \
        "the export reported the superseded registration, not the current one"
    b = le.build_bundle(KEY)
    r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
    assert r["ok"], r["checks"]


@test
def test_a_malformed_attribution_block_is_a_named_failure_not_a_traceback():
    """Audit finding 6. The docstring promises named failures, never a traceback;
    a recipient consuming --json gets nothing at all from one."""
    cases = [
        ("attribution is a string", lambda a: "not a dict"),
        ("key_id is a list", lambda a: {**a, "key_id": ["x"]}),
        ("attested_at is an int", lambda a: {**a, "attested_at": 5}),
        ("revoked_at is an int", lambda a: {**a, "revoked_at": 5}),
        ("attestation is null", lambda a: {**a, "attestation": None}),
    ]
    for label, mutate in cases:
        rows = fresh()
        registered_hoffman()
        at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
        b = le.build_bundle(KEY)
        a = b["records"][0]["attribution"]
        b["records"][0]["attribution"] = mutate(a)
        b = le.sign(b, KEY)
        try:
            r = le.verify_bundle(b, KEY, reviewer_keys={at.key_id(HOFFMAN): (HOFFMAN, "Hoffman")})
        except Exception as e:  # noqa: BLE001
            raise AssertionError("%s: backend verifier raised %r instead of "
                                 "reporting a failure" % (label, e))
        assert not r["ok"], "%s: accepted" % label
        code, sa = _run_standalone(b, KEY, (at.key_id(HOFFMAN), "Hoffman", HOFFMAN))
        assert "stderr" not in sa or sa.get("ok") is not None, \
            "%s: standalone verifier produced no JSON (traceback): %r" % (label, sa)
        assert code == 1 and not sa["ok"], "%s: standalone accepted it" % label


@test
def test_a_non_integer_attributed_records_is_a_named_failure():
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    b = le.build_bundle(KEY)
    b["manifest"]["attributed_records"] = "one"
    b = le.sign(b, KEY)
    r = le.verify_bundle(b, KEY)
    assert "attribution_count" in set(r["failed"]), r["failed"]
    code, sa = _run_standalone(b, KEY)
    assert code == 1 and "attribution_count" in sa["failed"], sa


@test
def test_a_revocation_ordering_tamper_is_caught_by_the_standalone_verifier():
    """
    Audit finding 9. The standalone verifier's revocation branch was reachable
    but no test drove it — disabling it left the suite green, so "32 of 32
    mutations killed" was true only of the mutations that were listed. This is
    the missing one.
    """
    rows = fresh()
    registered_hoffman()
    at.attest(store.DB_PATH, rows[0]["id"], HOFFMAN)
    at.revoke(store.DB_PATH, "Hoffman")
    b = le.build_bundle(KEY)
    b["records"][0]["attribution"]["revoked_at"] = "2000-01-01 00:00:00"
    b = le.sign(b, KEY)
    r = le.verify_bundle(b, KEY)
    assert "attribution_consistent" in set(r["failed"])
    code, sa = _run_standalone(b, KEY)
    assert code == 1 and "attribution_consistent" in sa["failed"], sa


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
