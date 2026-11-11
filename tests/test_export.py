"""
Tests for the signed ledger export (AD-3, part two).

The claim under test is not "export writes a file". It is: **a bundle that has
been altered in any of the ways an attacker would alter it fails verification,
and the failure names the check that caught it.** Every test below is an
attempt to forge, truncate, extend or re-sign a bundle and pass it off as
authentic. Most of them must be caught; the two that are NOT caught are
asserted to be not caught, because they are honest limits of the design rather
than bugs to fix (see `test_key_holder_can_forge__disclosed_limit`).

Run: python3 -I tests/test_export.py
"""

import copy
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_TMPDIR = tempfile.mkdtemp(prefix="axiom-export-test-")
os.environ["AXIOM_DB_PATH"] = os.path.join(_TMPDIR, "test.db")

from backend import ledger_export as le  # noqa: E402
from backend import store  # noqa: E402

RESULTS = []
KEY = b"\x11" * 32
OTHER_KEY = b"\x22" * 32


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001
        RESULTS.append((fn.__name__, False, exc))
    return fn


def fresh(n=3):
    """Ledger with n dispositions on distinct advisories, then return a bundle."""
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()
    for i in range(n):
        store.save_disposition(f"AD-2025-{i:04d}", f"Reviewer {i}", f"CERT-{i:03d}",
                               "concur_dispatch" if i % 2 == 0 else "request_inspection",
                               f"note {i}")
    return le.build_bundle(KEY)


def failed(result):
    return set(result["failed"])


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------
@test
def test_good_bundle_verifies():
    b = fresh()
    r = le.verify_bundle(b, KEY)
    assert r["ok"], r["checks"]
    assert r["failed"] == [], r["failed"]


@test
def test_bundle_carries_the_manifest_fields_d09_promises():
    """Partition boundary, record count, hash over contents — the three B01 §4.5 names."""
    b = fresh()
    m = b["manifest"]
    assert m["record_count"] == 3
    assert m["first_id"] == 1 and m["last_id"] == 3      # partition boundary
    assert m["head_hash"] == b["records"][-1]["record_hash"]   # hash over contents
    assert m["covered_fields"] == list(le.COVERED_FIELDS)
    assert m["ledger_chain_ok"] is True
    assert b["format"] == le.FORMAT


@test
def test_row_hash_reproduces_from_the_documented_field_list():
    """A foreign implementation must be able to recompute every hash."""
    b = fresh()
    for r in b["records"]:
        covered = {f: r[f] for f in le.COVERED_FIELDS}
        assert le.row_hash(covered) == r["record_hash"]
    # And the covered set is exactly the documented one — nothing quietly added,
    # nothing quietly dropped, in either direction.
    for r in b["records"]:
        for field in ("id", "record_hash"):
            assert field not in le.COVERED_FIELDS
        assert set(le.COVERED_FIELDS) <= set(r)


# ---------------------------------------------------------------------------
# Tampering with content
# ---------------------------------------------------------------------------
@test
def test_edited_note_is_detected():
    b = fresh()
    b["records"][1]["note"] = "note 1, but actually I approved it"
    r = le.verify_bundle(b, KEY)
    assert not r["ok"]
    assert {"row_hashes", "signature", "head_hash"} & failed(r), failed(r)


@test
def test_edited_disposition_is_detected():
    b = fresh()
    b["records"][0]["disposition"] = "deferred"
    assert not le.verify_bundle(b, KEY)["ok"]


@test
def test_edited_timestamp_is_detected():
    b = fresh()
    b["records"][0]["recorded_at"] = "2027-01-01 00:00:00"
    assert not le.verify_bundle(b, KEY)["ok"]


@test
def test_edited_reviewer_is_detected():
    b = fresh()
    b["records"][2]["reviewer_name"] = "Someone Else"
    assert not le.verify_bundle(b, KEY)["ok"]


@test
def test_relabelled_id_within_the_bundle_breaks_the_signature():
    """
    `id` is outside the row hash by design, so a swapped id does not break the
    per-row hashes — it is caught by the export signature and by the id-order
    and first_id checks. This asserts all three, because an earlier version of
    this test claimed the signature was "the only control", which was wrong:
    id_order and first_id also fire. A test whose stated rationale is untrue is
    a test that will mislead the next reader.
    """
    b = fresh()
    b["records"][0]["id"], b["records"][1]["id"] = b["records"][1]["id"], b["records"][0]["id"]
    r = le.verify_bundle(b, KEY)
    assert not r["ok"]
    assert "signature" in failed(r)
    assert "row_hashes" not in failed(r), (
        "expected the row hashes to still pass — id is not among the covered "
        "fields — which is why the export-level checks are load-bearing")
    assert {"id_order", "first_id"} & failed(r), (
        "the structural id checks should also fire, not just the signature")


# ---------------------------------------------------------------------------
# Truncation, removal, insertion
# ---------------------------------------------------------------------------
@test
def test_removed_record_is_detected():
    b = fresh()
    del b["records"][1]
    r = le.verify_bundle(b, KEY)
    assert not r["ok"]
    assert {"record_count", "prev_hash_links", "signature"} & failed(r), failed(r)


@test
def test_truncated_tail_is_detected():
    b = fresh()
    b["records"] = b["records"][:-1]
    r = le.verify_bundle(b, KEY)
    assert not r["ok"]
    assert {"record_count", "last_id", "head_hash", "signature"} & failed(r), failed(r)


@test
def test_added_forged_record_is_detected():
    b = fresh()
    forged = copy.deepcopy(b["records"][-1])
    forged["id"] = 4
    forged["note"] = "added after the fact"
    forged["prev_hash"] = b["records"][-1]["record_hash"]
    forged["record_hash"] = le.row_hash(forged)
    b["records"].append(forged)
    b["manifest"]["record_count"] = 4
    b["manifest"]["last_id"] = 4
    b["manifest"]["head_hash"] = forged["record_hash"]
    r = le.verify_bundle(b, KEY)
    # The forgery is internally consistent — a competent attacker re-hashes —
    # so only the signature can catch it. That is the control that matters.
    assert not r["ok"]
    assert "signature" in failed(r)


@test
def test_reordered_records_are_detected():
    b = fresh()
    b["records"][0], b["records"][1] = b["records"][1], b["records"][0]
    assert not le.verify_bundle(b, KEY)["ok"]


@test
def test_count_inflated_in_manifest_is_detected():
    b = fresh()
    b["manifest"]["record_count"] = 99
    assert "record_count" in failed(le.verify_bundle(b, KEY))


# ---------------------------------------------------------------------------
# Keys and signatures
# ---------------------------------------------------------------------------
@test
def test_wrong_key_is_named_as_a_key_problem_not_a_forgery():
    b = fresh()
    r = le.verify_bundle(b, OTHER_KEY)
    assert not r["ok"]
    assert "key_id" in failed(r) and "signature" in failed(r)
    detail = {c["name"]: c["detail"] for c in r["checks"]}["key_id"]
    assert "different key" in detail, detail


@test
def test_swapped_signature_value_is_detected():
    b = fresh()
    b["signature"]["value"] = "0" * 64
    assert "signature" in failed(le.verify_bundle(b, KEY))


@test
def test_tampered_manifest_is_detected():
    b = fresh()
    b["manifest"]["exported_at"] = "2020-01-01 00:00:00"
    assert "signature" in failed(le.verify_bundle(b, KEY))


@test
def test_stripped_signature_block_is_detected():
    b = fresh()
    del b["signature"]
    assert not le.verify_bundle(b, KEY)["ok"]


@test
def test_unknown_format_is_refused_not_guessed():
    b = fresh()
    b["format"] = "axiom-ledger-export/v99"
    r = le.verify_bundle(b, KEY)
    assert not r["ok"] and "format" in failed(r)


# ---------------------------------------------------------------------------
# A re-hashed ledger passes — the disclosed limit
# ---------------------------------------------------------------------------
@test
def test_wholly_rewritten_ledger_exports_a_fine_bundle__disclosed_limit():
    """
    This test asserts a DEFECTIVE outcome on purpose.

    If an attacker with file access rewrites every row and recomputes the whole
    chain, the exporting host sees a perfectly consistent ledger and signs a
    perfectly consistent bundle. Nothing in a single bundle can detect that.
    Only a *sequence* of bundles you already hold can — see the chaining tests
    below. Writing this down as a test keeps the limit from quietly becoming a
    forgotten caveat.
    """
    b = fresh()
    with store._connect() as conn:
        conn.execute("DROP TRIGGER dispositions_no_update")
        conn.execute("DROP TRIGGER dispositions_no_delete")
        rows = conn.execute("SELECT id FROM dispositions ORDER BY id").fetchall()
        prev = store.GENESIS_HASH
        for row in rows:
            rec = {
                "advisory_id": "AD-2025-0000",
                "reviewer_name": "Rewritten",
                "cert_id": "CERT-000",
                "disposition": "concur_dispatch",
                "note": "rewritten by someone with file access",
                "recorded_at": "2026-11-09 00:00:00",
                "supersedes_id": None,
                "prev_hash": prev,
            }
            rec["record_hash"] = store._compute_hash(rec)
            conn.execute(
                "UPDATE dispositions SET advisory_id=?, reviewer_name=?, cert_id=?, "
                "disposition=?, note=?, recorded_at=?, supersedes_id=?, prev_hash=?, "
                "record_hash=? WHERE id=?",
                (rec["advisory_id"], rec["reviewer_name"], rec["cert_id"],
                 rec["disposition"], rec["note"], rec["recorded_at"],
                 rec["supersedes_id"], rec["prev_hash"], rec["record_hash"], row["id"]))
            prev = rec["record_hash"]

    rewritten = le.build_bundle(KEY)
    r = le.verify_bundle(rewritten, KEY)
    assert r["ok"], "a re-hashed ledger produces a verifiable bundle — this is the known limit"
    assert rewritten["records"][0]["note"] == "rewritten by someone with file access"


@test
def test_chaining_detects_a_rewrite_between_two_exports():
    """
    The control that closes the limit above: hold bundle 1, then receive bundle
    2. If the ledger was rewritten in between, bundle 2's head does not extend
    bundle 1's — and bundle 2 cannot claim to, because what it would have to
    cite is bundle 1's digest, which the attacker cannot change in your copy.
    """
    b1 = fresh()
    # Legitimate growth.
    store.save_disposition("AD-2025-0003", "Reviewer 3", "CERT-003", "concur_dispatch")
    b2 = le.build_bundle(KEY, after_id=b1["manifest"]["last_id"],
                         previous_export_hash=le.signature_of(b1))
    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert r["ok"], r["failed"]

    # Now the same incremental bundle, but claiming to extend a bundle you never had.
    b3 = le.build_bundle(KEY, after_id=b1["manifest"]["last_id"],
                         previous_export_hash="f" * 64)
    r = le.verify_bundle(b3, KEY, previous_bundle=b1)
    assert not r["ok"] and "previous_export_link" in failed(r)


# ---------------------------------------------------------------------------
# Finding 1 (audit 2026-11-11): a rewritten history passed against a bundle
# the recipient already held. `no_truncation` compares ids only, so rewriting
# every record, recomputing the chain and exporting honestly left the head id
# unchanged and every check green. This test does the whole attack end to end.
# ---------------------------------------------------------------------------
def _rewrite_every_row(new_disposition="cleared_no_action"):
    """Simulate an attacker with file access and no key: drop the guards,
    rewrite every row, recompute the chain so it is internally consistent."""
    import sqlite3
    con = sqlite3.connect(store.DB_PATH)
    for t in ("dispositions_no_update", "dispositions_no_delete",
              "dispositions_no_replace"):
        con.execute(f"DROP TRIGGER IF EXISTS {t}")
    rows = con.execute(
        "SELECT id, advisory_id, reviewer_name, cert_id, recorded_at, note, "
        "supersedes_id FROM dispositions ORDER BY id").fetchall()
    prev = store.GENESIS_HASH
    for (rid, adv, rev, cert, when, note, sup) in rows:
        h = store._compute_hash({
            "advisory_id": adv, "reviewer_name": rev, "cert_id": cert,
            "disposition": new_disposition, "note": note,
            "recorded_at": when, "supersedes_id": sup, "prev_hash": prev})
        con.execute(
            "INSERT OR REPLACE INTO dispositions (id, advisory_id, "
            "reviewer_name, cert_id, disposition, note, recorded_at, "
            "supersedes_id, prev_hash, record_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (rid, adv, rev, cert, new_disposition, note, when, sup, prev, h))
        prev = h
    con.commit()
    con.close()


@test
def test_a_rewritten_history_is_caught_against_the_held_bundle():
    b1 = fresh()
    assert b1["records"][0]["disposition"] == "concur_dispatch"

    _rewrite_every_row()
    b2 = le.build_bundle(KEY, previous_export_hash=le.signature_of(b1))
    assert b2["records"][0]["disposition"] == "cleared_no_action"
    assert b2["manifest"]["backend_head_id"] == b1["manifest"]["backend_head_id"], \
        "head id must be unchanged, or this tests truncation instead"

    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert not r["ok"], "a rewritten history verified against the held bundle"
    assert "history_continues" in failed(r), r["failed"]
    # The row count did NOT fall — a rewrite preserves it. Assert that, so this
    # test cannot pass because `no_row_deletion` happened to fire instead.
    assert "no_row_deletion" not in failed(r), \
        "a rewrite must be caught by the anchor, not by a row-count drop"


@test
def test_a_rewritten_history_is_caught_by_the_standalone_verifier_too():
    """A recipient has the tool, not the repo. Same attack, other verifier."""
    b1 = fresh(2)
    _rewrite_every_row()
    b2 = le.build_bundle(KEY, previous_export_hash=le.signature_of(b1))

    d = tempfile.mkdtemp(prefix="axiom-rewrite-")
    p1, p2, kp = (os.path.join(d, n) for n in ("b1.json", "b2.json", "key"))
    for path, obj in ((p1, b1), (p2, b2)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
    with open(kp, "wb") as f:
        f.write(KEY)
    out = subprocess.run(
        [sys.executable, "-I", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
         "--bundle", p2, "--key-file", kp, "--previous-bundle", p1],
        capture_output=True, text=True, cwd=d)
    assert out.returncode != 0, "standalone verifier accepted a rewritten history"
    assert "history_continues" in out.stdout, out.stdout


@test
def test_a_deletion_from_the_middle_is_caught_by_the_row_count():
    """Head id unchanged, one fewer row: `no_truncation` cannot see it."""
    import sqlite3
    b1 = fresh(3)
    con = sqlite3.connect(store.DB_PATH)
    for t in ("dispositions_no_update", "dispositions_no_delete",
              "dispositions_no_replace"):
        con.execute(f"DROP TRIGGER IF EXISTS {t}")
    first = con.execute("SELECT record_hash FROM dispositions WHERE id=1").fetchone()[0]
    row = con.execute(
        "SELECT advisory_id, reviewer_name, cert_id, disposition, note, "
        "recorded_at, supersedes_id FROM dispositions WHERE id=3").fetchone()
    con.execute("DELETE FROM dispositions WHERE id=2")
    adv, rev, cert, disp, note, when, sup = row
    h = store._compute_hash({
        "advisory_id": adv, "reviewer_name": rev, "cert_id": cert,
        "disposition": disp, "note": note, "recorded_at": when,
        "supersedes_id": sup, "prev_hash": first})
    con.execute("UPDATE dispositions SET prev_hash=?, record_hash=? WHERE id=3",
                (first, h))
    con.commit()
    con.close()

    b2 = le.build_bundle(KEY, previous_export_hash=le.signature_of(b1))
    assert b2["manifest"]["backend_head_id"] == 3, "head must be unchanged"
    assert b2["manifest"]["ledger_rows"] < 3
    # Rewrite the ANCHOR RECORD itself (id 3) so `history_continues` also fails.
    # Without this the anchor check masks this one, and the test would pass with
    # `no_row_deletion` deleted.
    import sqlite3
    con = sqlite3.connect(store.DB_PATH)
    row3 = con.execute(
        "SELECT advisory_id, reviewer_name, cert_id, disposition, note, "
        "recorded_at, supersedes_id, prev_hash FROM dispositions WHERE id=3"
    ).fetchone()
    adv, rev, cert, disp, note, when, sup, ph = row3
    h3 = store._compute_hash({
        "advisory_id": adv, "reviewer_name": rev, "cert_id": cert,
        "disposition": disp, "note": "rewritten", "recorded_at": when,
        "supersedes_id": sup, "prev_hash": ph})
    con.execute("UPDATE dispositions SET note='rewritten', record_hash=? WHERE id=3", (h3,))
    con.commit()
    con.close()

    b2 = le.build_bundle(KEY, previous_export_hash=le.signature_of(b1))
    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert not r["ok"], "a mid-deletion + anchor rewrite must not verify"
    assert "no_row_deletion" in r["failed"], r["failed"]


@test
def test_a_bundle_carrying_a_duplicate_json_key_is_refused():
    """
    `json.load` keeps the LAST of two identical keys. A bundle with
    `"disposition": "CLEARED"` and a second `"disposition": "FLAGGED"` is read
    one way by the verifier and another by a first-key-wins viewer, with no
    check failing. Both CLIs must refuse the file outright.
    """
    b = fresh(1)
    d = tempfile.mkdtemp(prefix="axiom-dupkey-")
    kp, bp = os.path.join(d, "key"), os.path.join(d, "dup.json")
    with open(kp, "wb") as f:
        f.write(KEY)
    body = json.dumps(b, indent=2, sort_keys=True)
    assert '"note": "note 0"' in body, body
    body = body.replace('"note": "note 0"',
                        '"note": "CLEARED - nothing to see", "note": "note 0"', 1)
    with open(bp, "w", encoding="utf-8") as f:
        f.write(body)

    for cmd in ([sys.executable, "-I",
                 os.path.join(ROOT, "tools", "verify_ledger_export.py"),
                 "--bundle", bp, "--key-file", kp],
                # The in-repo CLI is a package module, so it runs with -m from
                # the repo root, not as a path. `-I` still isolates it.
                [sys.executable, "-m", "backend.ledger_export",
                 "verify", "--bundle", bp, "--key-file", kp]):
        out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        assert out.returncode != 0, "a duplicate-key bundle was accepted by: " + cmd[1]
        assert "duplicate key" in (out.stdout + out.stderr), out.stdout + out.stderr


@test
def test_insert_or_replace_over_an_existing_row_is_refused():
    """
    Finding 3 (audit 2026-11-11): `INSERT OR REPLACE` is an UPDATE that fires no
    DELETE trigger, so the first two guards missed it and every row of a live
    ledger could be rewritten with them installed. The schema now refuses it.
    """
    import sqlite3
    fresh(2)
    con = sqlite3.connect(store.DB_PATH)
    before = con.execute(
        "SELECT disposition FROM dispositions WHERE id=1").fetchone()[0]
    try:
        con.execute(
            "INSERT OR REPLACE INTO dispositions (id, advisory_id, reviewer_name, "
            "cert_id, disposition, note, recorded_at, supersedes_id, prev_hash, "
            "record_hash) VALUES (1,'AD-2025-0000','R','C','cleared_no_action',"
            "'x','2025-01-01','',  'a','b')")
        con.commit()
    except sqlite3.IntegrityError as exc:
        assert "INSERT OR REPLACE" in str(exc), exc
    else:
        raise AssertionError("INSERT OR REPLACE rewrote a ledger row")
    after = con.execute(
        "SELECT disposition FROM dispositions WHERE id=1").fetchone()[0]
    con.close()
    assert before == after, "the row changed despite the refusal"


# ---------------------------------------------------------------------------
# ERASURE — the gap the first build shipped with, found by audit
# ---------------------------------------------------------------------------
@test
def test_total_erasure_is_detected_when_chained():
    """
    THE ATTACK THAT BROKE THE FIRST VERSION OF THIS MODULE.

    Delete every row with file access, then run the honest exporter. Before the
    fix: `verify_chain()` truthfully reported "ok, 0 rows", the empty bundle was
    signed, `no_regression` short-circuited on a null `first_id`, and a
    recipient holding the previous bundle was told **everything passed** while
    every record they had ever been given had been destroyed.

    The fix records the ledger's own head (`backend_head_id`) in each bundle, so
    a later bundle cannot report a shorter ledger than one already delivered.
    """
    b1 = fresh()                       # three dispositions, ids 1..3
    assert b1["manifest"]["backend_head_id"] == 3

    with store._connect() as conn:     # attacker: file-level access, no key
        conn.execute("DROP TRIGGER dispositions_no_delete")
        conn.execute("DELETE FROM dispositions")

    b2 = le.build_bundle(KEY, previous_export_hash=le.signature_of(b1))
    assert b2["manifest"]["record_count"] == 0

    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert not r["ok"], "total erasure verified clean — the exact failure this test exists for"
    assert "no_truncation" in failed(r), failed(r)


@test
def test_head_records_deleted_is_detected_by_the_genesis_anchor():
    """Delete the first rows; the unbounded export no longer starts at genesis."""
    fresh()
    ids = [r["id"] for r in le._fetch(None, None)]
    with store._connect() as conn:
        conn.execute("DROP TRIGGER dispositions_no_delete")
        conn.execute("DELETE FROM dispositions WHERE id IN (?, ?)", (ids[0], ids[1]))
    b = le.build_bundle(KEY)
    r = le.verify_bundle(b, KEY)
    assert not r["ok"]
    assert "genesis_anchor" in failed(r), failed(r)


@test
def test_clean_tail_deletion_is_a_disclosed_limit_when_unchained():
    """
    Asserts a DEFECTIVE outcome on purpose, like the re-hash test above.

    Deleting only the newest rows leaves a perfectly valid chain, and the host
    truthfully reports a shorter ledger. Nothing in a single bundle can detect
    that — it takes a bundle you already hold. Documented, not papered over.
    """
    b1 = fresh()
    ids = [r["id"] for r in le._fetch(None, None)]
    with store._connect() as conn:
        conn.execute("DROP TRIGGER dispositions_no_delete")
        conn.execute("DELETE FROM dispositions WHERE id = ?", (ids[-1],))
    b2 = le.build_bundle(KEY)
    assert le.verify_bundle(b2, KEY)["ok"], "unchained tail deletion cannot be detected"

    # With the earlier bundle in hand, it is caught.
    b2c = le.build_bundle(KEY, previous_export_hash=le.signature_of(b1))
    assert not le.verify_bundle(b2c, KEY, previous_bundle=b1)["ok"]


@test
def test_zero_record_incremental_export_is_legitimate():
    """A quiet week produces an empty incremental bundle, and that must verify."""
    b1 = fresh()
    b2 = le.build_bundle(KEY, after_id=b1["manifest"]["last_id"],
                         previous_export_hash=le.signature_of(b1))
    assert b2["manifest"]["record_count"] == 0
    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert r["ok"], r["failed"]


@test
def test_inverted_range_is_refused_not_signed():
    fresh()
    try:
        le.build_bundle(KEY, after_id=99, to_id=1)
    except ValueError as exc:
        assert "empty range" in str(exc), exc
    else:
        raise AssertionError("an inverted range must be refused, not signed as empty")


# ---------------------------------------------------------------------------
# Malformed bundles produce verdicts, not tracebacks
# ---------------------------------------------------------------------------
@test
def test_malformed_bundles_never_raise():
    b = fresh()
    mutations = {
        "records as a dict": lambda x: x.__setitem__("records", {}),
        "manifest as a list": lambda x: x.__setitem__("manifest", []),
        "signature as a string": lambda x: x.__setitem__("signature", "x"),
        "record_count not a number": lambda x: x["manifest"].__setitem__("record_count", "abc"),
        "record id is null": lambda x: x["records"][0].__setitem__("id", None),
        "record not an object": lambda x: x["records"].__setitem__(0, "x"),
    }
    for label, mutate in mutations.items():
        corrupt = copy.deepcopy(b)
        mutate(corrupt)
        try:
            r = le.verify_bundle(corrupt, KEY)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(f"{label}: verifier raised {type(exc).__name__} instead "
                                 f"of returning a verdict: {exc}") from exc
        assert not r["ok"], f"{label}: malformed bundle verified clean"


@test
def test_keygen_force_does_not_leave_a_key_world_readable():
    """os.open's mode argument is ignored for an existing file; the fix chmods."""
    d = tempfile.mkdtemp(prefix="axiom-keymode-")
    kp = os.path.join(d, "k")
    with open(kp, "wb") as f:
        f.write(b"\x00" * 32)
    os.chmod(kp, 0o644)
    assert le.main(["keygen", "--key-file", kp, "--force"]) == 0
    mode = oct(os.stat(kp).st_mode & 0o777)
    assert mode == "0o600", f"key left at {mode} after --force"



@test
def test_bundle_that_does_not_forward_chain_is_detected():
    b1 = fresh()
    store.save_disposition("AD-2025-0009", "R", "C", "concur_dispatch")
    b2 = le.build_bundle(KEY)          # full re-export, no previous_export_hash
    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert not r["ok"] and "previous_export_link" in failed(r)


@test
def test_overlapping_incremental_bundle_is_detected():
    b1 = fresh()
    b2 = le.build_bundle(KEY, after_id=1, previous_export_hash=le.signature_of(b1))
    r = le.verify_bundle(b2, KEY, previous_bundle=b1)
    assert not r["ok"] and "no_regression" in failed(r)


# ---------------------------------------------------------------------------
# A broken ledger cannot be exported as a clean one
# ---------------------------------------------------------------------------
@test
def test_export_of_a_broken_ledger_says_so_and_fails_verification():
    fresh()
    with store._connect() as conn:
        conn.execute("DROP TRIGGER dispositions_no_update")
        conn.execute("UPDATE dispositions SET note='altered' WHERE id=2")
    b = le.build_bundle(KEY)
    assert b["manifest"]["ledger_chain_ok"] is False
    assert b["manifest"]["ledger_broken_at_id"] == 2
    r = le.verify_bundle(b, KEY)
    assert not r["ok"] and "ledger_chain_ok" in failed(r)


@test
def test_empty_ledger_exports_a_valid_empty_bundle():
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()
    b = le.build_bundle(KEY)
    assert b["manifest"]["record_count"] == 0
    assert b["manifest"]["head_hash"] == store.GENESIS_HASH
    r = le.verify_bundle(b, KEY)
    assert r["ok"], r["failed"]


# ---------------------------------------------------------------------------
# The standalone verifier — the one a recipient actually runs
# ---------------------------------------------------------------------------
def _run_standalone(bundle, key, previous=None):
    d = tempfile.mkdtemp(prefix="axiom-standalone-")
    bp = os.path.join(d, "bundle.json")
    kp = os.path.join(d, "key.bin")
    with open(bp, "w", encoding="utf-8") as f:
        json.dump(bundle, f)
    with open(kp, "wb") as f:
        f.write(key)
    cmd = [sys.executable, "-I", os.path.join(ROOT, "tools", "verify_ledger_export.py"),
           "--bundle", bp, "--key-file", kp, "--json"]
    if previous is not None:
        pp = os.path.join(d, "prev.json")
        with open(pp, "w", encoding="utf-8") as f:
            json.dump(previous, f)
        cmd += ["--previous-bundle", pp]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=d)
    return out.returncode, json.loads(out.stdout) if out.stdout.strip() else {"stderr": out.stderr}


@test
def test_standalone_verifier_accepts_a_good_bundle():
    b = fresh()
    code, result = _run_standalone(b, KEY)
    assert code == 0, result
    assert result["ok"], result["failed"]


@test
def test_standalone_verifier_rejects_a_tampered_bundle():
    b = fresh()
    b["records"][0]["note"] = "changed"
    code, result = _run_standalone(b, KEY)
    assert code == 1, result
    assert not result["ok"]


@test
def test_a_bundle_with_an_extra_top_level_field_is_rejected():
    """Found by trying it on 2026-11-10, not by reasoning about the code.

    The signature covers a selected tuple — ("format", "manifest", "records") —
    and the digest selected four named fields. Neither selected "everything
    else", so any added top-level key rode along unsigned and both verifiers
    reported ok=True. It matters because that key is not covered by the
    signature: it can be set after signing, and a recipient reading it would
    reasonably take it as attested. A body that is not exactly what was signed
    cannot be vouched for.
    """
    b = fresh()
    b["record_count"] = 99                      # plausible-looking, unsigned
    r = le.verify_bundle(b, KEY)
    assert not r["ok"], "a bundle with an unsigned extra field must not verify"
    assert "bundle_no_extras" in r["failed"], r["checks"]

    # The standalone verifier — the tool D09 names for the quarterly check —
    # must reject it too, not just the in-repo one.
    code, result = _run_standalone(b, KEY)
    assert code == 1, result
    assert "bundle_no_extras" in result["failed"], result["checks"]


@test
def test_standalone_verifier_rejects_the_wrong_key():
    b = fresh()
    code, result = _run_standalone(b, OTHER_KEY)
    assert code == 1 and "key_id" in result["failed"], result


@test
def test_standalone_verifier_runs_without_the_database_present():
    """
    The recipient has the bundle and the key. They do not have the database,
    and they must not need it. `_run_standalone` runs from a fresh temp cwd
    with `-I`, so nothing the verifier imports could resolve to `backend/`;
    this asserts the stronger fact — the module imports no database code at all.
    """
    b = fresh()
    code, result = _run_standalone(b, KEY)
    assert code == 0, result
    src = open(os.path.join(ROOT, "tools", "verify_ledger_export.py"),
               encoding="utf-8").read()
    for forbidden in ("import sqlite3", "from backend", "import backend", "AXIOM_DB_PATH"):
        assert forbidden not in src, f"standalone verifier must not reference {forbidden!r}"


@test
def test_standalone_verifier_chains_bundles():
    b1 = fresh()
    store.save_disposition("AD-2025-0100", "R", "C", "concur_dispatch")
    b2 = le.build_bundle(KEY, after_id=b1["manifest"]["last_id"],
                         previous_export_hash=le.signature_of(b1))
    code, result = _run_standalone(b2, KEY, previous=b1)
    assert code == 0, result


@test
def test_standalone_verifier_and_backend_agree_on_genesis_hash():
    """
    A specific divergence: only the standalone verifier once checked
    `genesis_hash`, so a bundle with a rewritten genesis value passed in-repo
    and failed standalone. Two verifiers that disagree make a 'verified' bundle
    useless, so both check it now and this asserts they agree.
    """
    b = fresh()
    b["manifest"]["genesis_hash"] = "f" * 64      # rewrite, then re-sign so only this check fires
    b = le.sign({k: b[k] for k in ("format", "manifest", "records")}, KEY)
    in_repo = le.verify_bundle(b, KEY)["ok"]
    code, _ = _run_standalone(b, KEY)
    assert in_repo == (code == 0), f"backend={in_repo} standalone={code == 0}"
    assert in_repo is False, "a rewritten genesis_hash must fail in both"


@test
def test_zero_record_incremental_verifies_standalone_too():
    """The quiet-week bundle must pass both implementations, not just one."""
    b1 = fresh()
    b2 = le.build_bundle(KEY, after_id=b1["manifest"]["last_id"],
                         previous_export_hash=le.signature_of(b1))
    code, result = _run_standalone(b2, KEY, previous=b1)
    assert code == 0, result


@test
def test_standalone_verifier_and_backend_agree_on_every_case():
    """Two independent implementations must not diverge — that is the whole point."""
    cases = []
    b = fresh()
    cases.append(("good", b))

    t = copy.deepcopy(b); t["records"][1]["disposition"] = "x"; cases.append(("content", t))
    t = copy.deepcopy(b); del t["records"][0]; cases.append(("removed", t))
    t = copy.deepcopy(b); t["manifest"]["record_count"] = 2; cases.append(("count", t))
    t = copy.deepcopy(b); t["signature"]["value"] = "a" * 64; cases.append(("sig", t))

    for name, bundle in cases:
        in_repo = le.verify_bundle(bundle, KEY)["ok"]
        code, _ = _run_standalone(bundle, KEY)
        assert in_repo == (code == 0), f"{name}: backend={in_repo} standalone={code == 0}"


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
@test
def test_cli_export_and_verify_round_trip():
    fresh()
    d = tempfile.mkdtemp(prefix="axiom-cli-")
    kp = os.path.join(d, "signer.key")
    bp = os.path.join(d, "export.json")

    assert le.main(["keygen", "--key-file", kp]) == 0
    assert os.path.getsize(kp) == 32
    assert le.main(["keygen", "--key-file", kp]) == 2, "must refuse to clobber a key"

    assert le.main(["export", "--key-file", kp, "--out", bp]) == 0
    assert os.path.exists(bp + ".sha256")
    assert le.main(["verify", "--key-file", kp, "--bundle", bp]) == 0


@test
def test_cli_export_after_id_is_incremental():
    b = fresh()
    d = tempfile.mkdtemp(prefix="axiom-cli-inc-")
    kp = os.path.join(d, "k")
    with open(kp, "wb") as f:
        f.write(KEY)
    bp = os.path.join(d, "inc.json")
    assert le.main(["export", "--key-file", kp, "--out", bp,
                    "--after-id", str(b["manifest"]["last_id"]),
                    "--previous-export-hash", le.signature_of(b)]) == 0
    with open(bp, encoding="utf-8") as f:
        inc = json.load(f)
    assert inc["manifest"]["record_count"] == 0
    assert inc["manifest"]["previous_export_hash"] == le.signature_of(b)


@test
def test_key_file_of_wrong_length_is_refused():
    d = tempfile.mkdtemp(prefix="axiom-badkey-")
    kp = os.path.join(d, "short")
    with open(kp, "wb") as f:
        f.write(b"too short")
    try:
        le.load_key(kp)
    except ValueError as exc:
        assert "32 raw bytes" in str(exc), exc
    else:
        raise AssertionError("a 9-byte key must be refused, not hashed and used")


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
