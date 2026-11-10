"""
Tests for the append-only disposition ledger (AD-3).

These are adversarial on purpose. The claim being tested is not "save_disposition
works" but "this ledger cannot silently lose an earlier decision", so most of
these tests try to lose one and assert that the attempt fails.

Run: python3 -I tests/test_store.py
"""

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point the store at a throwaway file before importing it.
_TMPDIR = tempfile.mkdtemp(prefix="axiom-store-test-")
os.environ["AXIOM_DB_PATH"] = os.path.join(_TMPDIR, "test.db")

from backend import store  # noqa: E402

RESULTS = []


def test(fn):
    try:
        fn()
        RESULTS.append((fn.__name__, True, None))
    except Exception as exc:  # noqa: BLE001 - reporting, not swallowing
        RESULTS.append((fn.__name__, False, exc))
    return fn


def fresh():
    """Empty ledger for one test."""
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()


# ---------------------------------------------------------------------------
# Baseline behaviour
# ---------------------------------------------------------------------------
@test
def test_first_disposition_is_recorded():
    fresh()
    rec = store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001", "concur_dispatch")
    assert rec["id"] == 1, rec
    assert rec["supersedes_id"] is None, rec
    assert rec["prev_hash"] == store.GENESIS_HASH, rec
    assert store.ledger_size() == 1


@test
def test_current_disposition_round_trips():
    fresh()
    store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001", "concur_dispatch")
    got = store.get_disposition("AD-2025-0001")
    assert got is not None
    assert got["disposition"] == "concur_dispatch"
    assert got["reviewer_name"] == "A. Reviewer"
    assert got["cert_id"] == "CERT-001"
    assert got["supersedes_id"] is None


@test
def test_unknown_advisory_returns_none():
    fresh()
    assert store.get_disposition("AD-9999-9999") is None


# ---------------------------------------------------------------------------
# The core property: a second decision supersedes, it does not replace
# ---------------------------------------------------------------------------
@test
def test_second_disposition_supersedes_rather_than_overwrites():
    fresh()
    first = store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001",
                                   "concur_dispatch", note="Initial call")
    second = store.save_disposition("AD-2025-0001", "B. Reviewer", "CERT-002",
                                    "reject_sensor", note="Sensor flagged on inspection")

    assert store.ledger_size() == 2, "the earlier row must survive"
    assert second["id"] != first["id"], "a second decision must be a new row"
    assert second["supersedes_id"] == first["id"], second

    chain = store.disposition_history("AD-2025-0001")
    assert [r["disposition"] for r in chain] == ["concur_dispatch", "reject_sensor"]
    assert chain[0]["note"] == "Initial call"
    assert chain[1]["note"] == "Sensor flagged on inspection"


@test
def test_first_recorded_at_survives_a_later_decision():
    """The specific thing the old upsert destroyed."""
    fresh()
    first = store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001", "concur_dispatch")
    store.save_disposition("AD-2025-0001", "B. Reviewer", "CERT-002", "escalate")

    chain = store.disposition_history("AD-2025-0001")
    assert chain[0]["recorded_at"] == first["recorded_at"]
    assert chain[0]["reviewer_name"] == "A. Reviewer"


@test
def test_current_read_returns_latest_not_first():
    fresh()
    store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001", "concur_dispatch")
    store.save_disposition("AD-2025-0001", "B. Reviewer", "CERT-002", "escalate")
    cur = store.get_disposition("AD-2025-0001")
    assert cur["disposition"] == "escalate"
    assert cur["reviewer_name"] == "B. Reviewer"


@test
def test_third_decision_chains_to_the_second():
    fresh()
    a = store.save_disposition("AD-2025-0001", "A", "C1", "concur_dispatch")
    b = store.save_disposition("AD-2025-0001", "B", "C2", "escalate")
    c = store.save_disposition("AD-2025-0001", "C", "C3", "override_downgrade")
    assert c["supersedes_id"] == b["id"]
    assert b["supersedes_id"] == a["id"]
    assert store.ledger_size() == 3


# ---------------------------------------------------------------------------
# The schema refuses mutation, whoever is asking
# ---------------------------------------------------------------------------
@test
def test_update_is_refused_by_the_database():
    fresh()
    store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001", "concur_dispatch")

    conn = sqlite3.connect(store.DB_PATH)
    try:
        try:
            conn.execute("UPDATE dispositions SET disposition='escalate' WHERE id=1")
            raise AssertionError("UPDATE was allowed — the append-only guard is missing")
        except sqlite3.DatabaseError as exc:
            assert "append-only" in str(exc).lower(), exc
    finally:
        conn.close()

    assert store.get_disposition("AD-2025-0001")["disposition"] == "concur_dispatch"


@test
def test_delete_is_refused_by_the_database():
    fresh()
    store.save_disposition("AD-2025-0001", "A. Reviewer", "CERT-001", "concur_dispatch")

    conn = sqlite3.connect(store.DB_PATH)
    try:
        try:
            conn.execute("DELETE FROM dispositions WHERE id=1")
            raise AssertionError("DELETE was allowed — the append-only guard is missing")
        except sqlite3.DatabaseError as exc:
            assert "append-only" in str(exc).lower(), exc
    finally:
        conn.close()

    assert store.ledger_size() == 1


@test
def test_triggers_survive_reopening_the_database():
    """init_db on an existing ledger must not drop the guards."""
    fresh()
    store.save_disposition("AD-2025-0001", "A", "C1", "concur_dispatch")
    store.init_db()  # second call, as happens on every process start

    conn = sqlite3.connect(store.DB_PATH)
    try:
        try:
            conn.execute("DELETE FROM dispositions")
            raise AssertionError("guards were lost on re-init")
        except sqlite3.DatabaseError:
            pass
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# The hash chain
# ---------------------------------------------------------------------------
@test
def test_chain_verifies_when_untouched():
    fresh()
    store.save_disposition("AD-2025-0001", "A", "C1", "concur_dispatch")
    store.save_disposition("AD-2025-0002", "B", "C2", "escalate")
    store.save_disposition("AD-2025-0001", "C", "C3", "reject_sensor")

    result = store.verify_chain()
    assert result["ok"] is True, result
    assert result["rows"] == 3


@test
def test_chain_links_each_row_to_the_previous():
    fresh()
    a = store.save_disposition("AD-1", "A", "C1", "concur_dispatch")
    b = store.save_disposition("AD-2", "B", "C2", "escalate")
    assert a["prev_hash"] == store.GENESIS_HASH
    assert b["prev_hash"] == a["record_hash"]


@test
def test_tampered_row_is_detected():
    """The triggers stop UPDATE through the engine; this tests detection of a
    row changed by something that bypassed them, which is the real threat."""
    fresh()
    store.save_disposition("AD-1", "A", "C1", "concur_dispatch")
    store.save_disposition("AD-2", "B", "C2", "escalate")

    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("DROP TRIGGER dispositions_no_update")
        conn.execute("UPDATE dispositions SET reviewer_name='Mallory' WHERE id=2")
        conn.commit()
    finally:
        conn.close()

    result = store.verify_chain()
    assert result["ok"] is False, result
    assert result["broken_at_id"] == 2
    assert "altered" in result["reason"]


@test
def test_removed_row_is_detected():
    fresh()
    store.save_disposition("AD-1", "A", "C1", "concur_dispatch")
    store.save_disposition("AD-2", "B", "C2", "escalate")
    store.save_disposition("AD-3", "C", "C3", "reject_sensor")

    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("DROP TRIGGER dispositions_no_delete")
        conn.execute("DELETE FROM dispositions WHERE id=2")
        conn.commit()
    finally:
        conn.close()

    result = store.verify_chain()
    assert result["ok"] is False, result
    assert result["broken_at_id"] == 3
    assert "prev_hash" in result["reason"]


# ---------------------------------------------------------------------------
# Migration from the v1 one-row-per-advisory schema
# ---------------------------------------------------------------------------
@test
def test_v1_table_migrates_without_losing_the_existing_decision():
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)

    # Recreate the v1 schema exactly as it shipped.
    conn = sqlite3.connect(store.DB_PATH)
    conn.execute("""
        CREATE TABLE dispositions (
            advisory_id TEXT PRIMARY KEY,
            reviewer_name TEXT NOT NULL,
            cert_id TEXT NOT NULL,
            disposition TEXT NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute(
        "INSERT INTO dispositions VALUES ('AD-2025-0007','Legacy Reviewer','CERT-9','escalate','2026-11-01 10:00:00')"
    )
    conn.commit()
    conn.close()

    store.init_db()

    got = store.get_disposition("AD-2025-0007")
    assert got is not None, "migration lost the row"
    assert got["disposition"] == "escalate"
    assert got["reviewer_name"] == "Legacy Reviewer"
    assert got["recorded_at"] == "2026-11-01 10:00:00", "timestamp must not be rewritten"
    assert got["supersedes_id"] is None
    assert got["prev_hash"] == store.GENESIS_HASH
    assert store.verify_chain()["ok"] is True


@test
def test_migration_preserves_multiple_advisories():
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)

    conn = sqlite3.connect(store.DB_PATH)
    conn.execute("""
        CREATE TABLE dispositions (
            advisory_id TEXT PRIMARY KEY,
            reviewer_name TEXT NOT NULL,
            cert_id TEXT NOT NULL,
            disposition TEXT NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    for i, disp in enumerate(["concur_dispatch", "escalate", "reject_sensor"], start=1):
        conn.execute(
            "INSERT INTO dispositions VALUES (?,?,?,?,?)",
            (f"AD-2025-000{i}", f"R{i}", f"C{i}", disp, f"2026-11-0{i} 09:00:00"),
        )
    conn.commit()
    conn.close()

    store.init_db()

    assert store.ledger_size() == 3
    assert store.verify_chain()["ok"] is True
    assert store.get_disposition("AD-2025-0001")["disposition"] == "concur_dispatch"
    assert store.get_disposition("AD-2025-0003")["disposition"] == "reject_sensor"


@test
def test_migration_is_idempotent():
    fresh()
    store.save_disposition("AD-1", "A", "C1", "concur_dispatch")
    before = store.ledger_size()
    store.init_db()
    store.init_db()
    assert store.ledger_size() == before


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    width = max(len(n) for n, _, _ in RESULTS)
    failed = 0
    for name, ok, exc in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}" + (f"  {exc!r}" if exc else ""))
        if not ok:
            failed += 1
    print(f"\n{len(RESULTS) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
