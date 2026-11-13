"""
SQLite-backed, append-only persistence for reviewer dispositions.

Implements AD-3 (B01 §2): a disposition may be superseded but never overwritten
and never deleted. Three layers enforce that, and each one is load-bearing:

1. **No UPDATE or DELETE path in Python.** There is no function here that
   mutates a row. A correction is a new row carrying `supersedes_id`, which
   points at the row it corrects. Both rows survive.

2. **Database-level triggers.** Even someone holding the sqlite3 CLI, or a
   future contributor who adds an innocent-looking UPDATE, is stopped:
   `BEFORE UPDATE` and `BEFORE DELETE` on the ledger raise ABORT. The Python
   layer is not the guarantee; the schema is.

3. **A hash chain.** Each row carries `prev_hash` (the previous row's
   `record_hash`, or 64 zeros for the first) and `record_hash`, a SHA-256 over
   the row's own content plus `prev_hash`. Editing a row in place therefore
   breaks its own hash, and deleting one breaks the next row's `prev_hash`.
   `verify_chain()` recomputes the whole chain and reports the first row that
   fails.

What this does and does not prove — state it plainly rather than implying more:

- It **does** prove the ledger has not been altered *by anything that went
  through this database*. An attacker with write access to the file can drop the
  triggers, rewrite rows and recompute every hash; the chain is a tamper-*evident*
  control, not tamper-*proof*.
- It **does** make an accidental overwrite impossible rather than merely
  discouraged, which is what the old upsert allowed.
- It does **not** replicate off-box. A destroyed disk still destroys the
  ledger. Signed export is now built (`backend/ledger_export.py`); automatic
  replication is not, and a bundle only helps if somebody keeps it
  (`backend/ledger_export.py` module docstring, B01 §4.5a, D09 §4.4).

Deliberately the stdlib `sqlite3` module — no new dependency, no server
process, one file that survives a restart.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional

DB_PATH = os.environ.get("AXIOM_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "axiom.db"))

GENESIS_HASH = "0" * 64

SCHEMA_VERSION = 2


# Seconds a connection waits for a competing writer before raising. With rollback
# journal (the SQLite default) a writer holds an exclusive lock for the whole
# commit, so two concurrent disposition writes on a busy box would otherwise fail
# immediately with "database is locked" rather than queueing.
_BUSY_TIMEOUT_S = 30.0


def _configure(conn):
    """
    Set the pragmas every connection needs, on every connection.

    WAL is set here rather than once at creation because journal_mode is a
    property of the *database file*, but a connection opened before it is set
    still runs in rollback journal — and `sqlite3.connect` does not read a
    config file. Setting it per connection is idempotent and cheap.

    Why WAL at all: B01 §4/§5 and B02 both describe the ledger as WAL, and the
    failure mode claimed for it ("edge box loses power: SQLite WAL recovers
    committed dispositions") depends on it. Until 2026-11-13 the code never set
    it, so the docket described a mode the file was not in. Readers and the
    single writer can then proceed concurrently, and a committed transaction
    survives an abrupt power loss without the reader having to wait for it.

    `synchronous=NORMAL` is the pairing WAL is normally used with, and it is a
    deliberate choice recorded here rather than an accident: in WAL mode it puts
    a commit at risk only of the last transaction on a power cut under a
    non-checkpointing OS, and this ledger's durability claim is about committed
    records surviving, which WAL+NORMAL still provides on the box this ships to.
    """
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=%d" % int(_BUSY_TIMEOUT_S * 1000))


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _configure(conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Chain arithmetic
# ---------------------------------------------------------------------------
def _row_payload(row: Dict[str, object]) -> str:
    """
    Canonical serialisation of the fields the hash covers.

    `sort_keys=True`, no whitespace, fixed separators — so the same row always
    hashes the same way and a verifier in another language can reproduce it
    from the documented field list. `record_hash` is excluded, obviously.
    """
    covered = {
        "advisory_id": row["advisory_id"],
        "reviewer_name": row["reviewer_name"],
        "cert_id": row["cert_id"],
        "disposition": row["disposition"],
        "note": row["note"],
        "recorded_at": row["recorded_at"],
        "supersedes_id": row["supersedes_id"],
        "prev_hash": row["prev_hash"],
    }
    return json.dumps(covered, sort_keys=True, separators=(",", ":"))


def _compute_hash(row: Dict[str, object]) -> str:
    return hashlib.sha256(_row_payload(row).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def init_db():
    """
    Create the ledger and its guard triggers, and migrate a v1 table in place.

    The v1 schema was `dispositions(advisory_id PRIMARY KEY, ...)` — one row per
    advisory, overwritten on re-decision. A v1 row held the *latest* decision
    and nothing else. Migration keeps that decision, marks it as the first link
    in the chain, and cannot invent history it never had; the timestamps of any
    prior overwrites are already gone and are not fabricated.
    """
    with _connect() as conn:
        existing = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='dispositions'"
        ).fetchone()

        legacy = None
        if existing is not None:
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(dispositions)").fetchall()}
            if "record_hash" not in cols:
                # Rename out of the way only; the new table is created below by
                # the same CREATE statement used for a fresh install, so there is
                # exactly one definition of the schema.
                conn.execute("ALTER TABLE dispositions RENAME TO dispositions_v1")
                legacy = "dispositions_v1"

        conn.execute("""
            CREATE TABLE IF NOT EXISTS dispositions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                advisory_id   TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                cert_id       TEXT NOT NULL,
                disposition   TEXT NOT NULL,
                note          TEXT NOT NULL DEFAULT '',
                recorded_at   TEXT NOT NULL,
                supersedes_id INTEGER REFERENCES dispositions(id),
                prev_hash     TEXT NOT NULL,
                record_hash   TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dispositions_advisory
            ON dispositions (advisory_id, id)
        """)

        if legacy is not None:
            _migrate_v1(conn, legacy)

        # Guard triggers. `IF NOT EXISTS` so re-running init_db is harmless.
        # DROP TRIGGER is itself possible for someone with file access — see the
        # module docstring on what the chain does and does not prove.
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS dispositions_no_update
            BEFORE UPDATE ON dispositions
            BEGIN
                SELECT RAISE(ABORT, 'disposition ledger is append-only: UPDATE is not permitted (AD-3)');
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS dispositions_no_delete
            BEFORE DELETE ON dispositions
            BEGIN
                SELECT RAISE(ABORT, 'disposition ledger is append-only: DELETE is not permitted (AD-3)');
            END
        """)
        # `INSERT OR REPLACE` is an UPDATE wearing a different hat: SQLite
        # resolves the conflict by deleting the existing row and inserting a
        # new one, and the implicit delete does NOT fire a DELETE trigger.
        # Both guards above therefore miss it, and the "append-only" claim is
        # false. Found by audit 2026-11-11 — every row of a live ledger was
        # rewritten to a different disposition with all triggers installed.
        #
        # A BEFORE INSERT guard that refuses an id already present closes it:
        # the check runs before conflict resolution, so there is nothing left
        # for OR REPLACE to replace.
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS dispositions_no_replace
            BEFORE INSERT ON dispositions
            WHEN EXISTS (SELECT 1 FROM dispositions WHERE id = NEW.id)
            BEGIN
                SELECT RAISE(ABORT, 'disposition ledger is append-only: INSERT OR REPLACE over an existing row is not permitted (AD-3)');
            END
        """)

        conn.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)


def _migrate_v1(conn, legacy: str):
    """Convert the v1 one-row-per-advisory table into an append-only ledger."""
    rows = conn.execute(
        f"SELECT advisory_id, reviewer_name, cert_id, disposition, recorded_at "
        f"FROM {legacy} ORDER BY recorded_at, advisory_id"
    ).fetchall()

    prev = GENESIS_HASH
    for r in rows:
        rec = {
            "advisory_id": r["advisory_id"],
            "reviewer_name": r["reviewer_name"],
            "cert_id": r["cert_id"],
            "disposition": r["disposition"],
            "note": "",
            "recorded_at": r["recorded_at"],
            "supersedes_id": None,
            "prev_hash": prev,
        }
        rec["record_hash"] = _compute_hash(rec)
        conn.execute(
            """
            INSERT INTO dispositions
                (advisory_id, reviewer_name, cert_id, disposition, note,
                 recorded_at, supersedes_id, prev_hash, record_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rec["advisory_id"], rec["reviewer_name"], rec["cert_id"],
             rec["disposition"], rec["note"], rec["recorded_at"],
             None, rec["prev_hash"], rec["record_hash"]),
        )
        prev = rec["record_hash"]

    conn.execute(f"DROP TABLE {legacy}")


# ---------------------------------------------------------------------------
# Writes — insert only
# ---------------------------------------------------------------------------
def save_disposition(advisory_id: str, reviewer_name: str, cert_id: str,
                     disposition: str, note: str = "",
                     guard=None, attest=None) -> Dict[str, object]:
    """
    Append a disposition. Never updates.

    A second decision on the same advisory becomes a new row whose
    `supersedes_id` names the row it replaces. The earlier row keeps its own
    timestamp and content and remains readable.

    Runs under BEGIN IMMEDIATE so two concurrent appends cannot both read the
    same `prev_hash` and fork the chain.

    `guard`, when supplied, is called **inside that transaction, before the
    INSERT**. It may raise to abort the append, **or return a falsy value** to
    abort it; whatever it raises propagates and the transaction rolls back. This
    exists for the AD-2 entry check: the caller verifies the reviewer's
    certification is still live, and a revocation landing between that check and
    this INSERT would otherwise record a decision under a certificate that no
    longer exists. The ledger's own write lock is the only place where "still
    live" and "still unwritten" can be true at the same instant — so the
    re-check belongs here rather than in the route.

    **Returning False must abort, and originally did not.** The first version
    read `if guard is not None: guard()` and discarded the result, while the
    route passed `lambda: accounts.cert_is_live(...)`, which returns a bool. The
    guard therefore ran, computed False, and the row was written anyway. The
    suite did not catch it because the tests simulated the race with a guard that
    *raised*, which is not the guard the route actually installs. A guard whose
    only tested failure mode is one the caller does not use is not a guard.
    Found by adversarial audit 2026-11-11, after 310 green tests.

    `attest`, when supplied, is called as `attest(conn, rec)` **after the INSERT
    and before COMMIT**, inside the same transaction. It exists so that entry
    requires a live reviewer key: the attestation is written with the row or not
    at all. A refused key therefore leaves no disposition — there is no window in
    which a row exists that no key vouched for, and no state where the operator
    sees success and the recipient's verifier rejects the bundle.

    `save_disposition` deliberately does not import `attribution`: the ledger is
    the lower module and attribution reads it. The route supplies the callable.
    """
    with _connect_atomic() as conn:
        if guard is not None:
            if guard() is False:
                raise ValueError(
                    "the write guard refused this append (the condition it "
                    "checked became false before the row was written)")
        prev = conn.execute(
            "SELECT record_hash FROM dispositions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev["record_hash"] if prev else GENESIS_HASH

        prior = conn.execute(
            "SELECT id FROM dispositions WHERE advisory_id = ? ORDER BY id DESC LIMIT 1",
            (advisory_id,),
        ).fetchone()

        recorded_at = conn.execute("SELECT datetime('now') AS t").fetchone()["t"]

        rec = {
            "advisory_id": advisory_id,
            "reviewer_name": reviewer_name,
            "cert_id": cert_id,
            "disposition": disposition,
            "note": note,
            "recorded_at": recorded_at,
            "supersedes_id": prior["id"] if prior else None,
            "prev_hash": prev_hash,
        }
        rec["record_hash"] = _compute_hash(rec)

        cur = conn.execute(
            """
            INSERT INTO dispositions
                (advisory_id, reviewer_name, cert_id, disposition, note,
                 recorded_at, supersedes_id, prev_hash, record_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rec["advisory_id"], rec["reviewer_name"], rec["cert_id"],
             rec["disposition"], rec["note"], rec["recorded_at"],
             rec["supersedes_id"], rec["prev_hash"], rec["record_hash"]),
        )
        rec["id"] = cur.lastrowid
        if attest is not None:
            # Inside the transaction on purpose: raising here rolls back the
            # INSERT above, so an unverifiable key leaves the ledger untouched.
            rec["attestation"] = attest(conn, dict(rec))
        return dict(rec)


@contextmanager
def _connect_atomic():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # Same pragmas as the plain path. Without busy_timeout here a second writer
    # waiting on BEGIN IMMEDIATE would fail instantly rather than queue, which is
    # the concurrency hole WAL is meant to close.
    _configure(conn)
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
def get_disposition(advisory_id: str) -> Optional[Dict[str, object]]:
    """The current (latest) disposition for one advisory, or None."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, advisory_id, reviewer_name, cert_id, disposition, note,
                   recorded_at, supersedes_id, prev_hash, record_hash
            FROM dispositions WHERE advisory_id = ? ORDER BY id DESC LIMIT 1
            """,
            (advisory_id,),
        ).fetchone()
    return dict(row) if row else None


def disposition_history(advisory_id: str) -> List[Dict[str, object]]:
    """Every disposition ever recorded for one advisory, oldest first."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, advisory_id, reviewer_name, cert_id, disposition, note,
                   recorded_at, supersedes_id, prev_hash, record_hash
            FROM dispositions WHERE advisory_id = ? ORDER BY id ASC
            """,
            (advisory_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def all_dispositions() -> Dict[str, Dict[str, object]]:
    """Current disposition per advisory — the shape callers already expect."""
    out: Dict[str, Dict[str, object]] = {}
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, advisory_id, reviewer_name, cert_id, disposition, note,
                   recorded_at, supersedes_id, prev_hash, record_hash
            FROM dispositions ORDER BY id ASC
            """
        ).fetchall()
    for r in rows:
        out[r["advisory_id"]] = dict(r)
    return out


def ledger_size() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM dispositions").fetchone()["n"]


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def verify_chain() -> Dict[str, object]:
    """
    Recompute the whole chain. Returns
        {"ok": bool, "rows": n, "broken_at_id": int|None, "reason": str|None}

    Detects: a row whose content was changed (its own hash stops matching), a
    row removed from the middle (the next row's prev_hash no longer matches),
    and a chain whose links point at nothing.
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, advisory_id, reviewer_name, cert_id, disposition, note,
                   recorded_at, supersedes_id, prev_hash, record_hash
            FROM dispositions ORDER BY id ASC
            """
        ).fetchall()

    expected_prev = GENESIS_HASH
    for r in rows:
        rec = dict(r)
        if rec["prev_hash"] != expected_prev:
            return {"ok": False, "rows": len(rows), "broken_at_id": rec["id"],
                    "reason": "prev_hash does not match the preceding row "
                              "(a row was inserted, removed or reordered)"}
        if _compute_hash(rec) != rec["record_hash"]:
            return {"ok": False, "rows": len(rows), "broken_at_id": rec["id"],
                    "reason": "record_hash does not match the row content "
                              "(the row was altered)"}
        expected_prev = rec["record_hash"]

    return {"ok": True, "rows": len(rows), "broken_at_id": None, "reason": None}
