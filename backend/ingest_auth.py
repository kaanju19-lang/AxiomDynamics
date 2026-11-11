"""
Ingest authentication - the inbound collector path, B01 item 5.

A collector sending detector payloads is not a reviewer making a disposition.
The credential model is intentionally separate:

- Reviewer (accounts.py): local account bound to a issued certification,
  PBKDF2-HMAC-SHA256 verifier, bearer token with a TTL measured in hours.
  Proves a person and a credential at sign-in time. Revocation of the
  underlying cert stops the token from writing. Transient.

- Collector (this module): named enrollment bound to no certification,
  ephemeral bearer token with no TTL. Proves only that the caller holds the
  token. Revocation stops issuing new tokens but does not invalidate existing
  ones - the collector is scheduled software, not a person who just left, and
  stopping an automated process retroactively is usually wrong. Long-lived.

The collector token is a 32-byte secret returned once at enrollment and never
again. The issuer stores only the SHA-256 digest. On each ingest the caller
presents the token and the route verifies the digest against the store.

Like accounts.py, the registry is append-only and hash-chained. Enrollments
and revocations are immutable records, not edits. A live enrollment is one
for which no revocation exists.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

AUTH_NONE = "none"
AUTH_REQUIRED = "required"

TOKEN_SIZE_BYTES = 32

COLLECTOR_DDL = """
CREATE TABLE IF NOT EXISTS ingest_collectors (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    note       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_at TEXT,
    prev_hash  TEXT NOT NULL,
    entry_hash TEXT NOT NULL
);
"""

COLLECTOR_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS ingest_collectors_no_update
    BEFORE UPDATE ON ingest_collectors
    BEGIN SELECT RAISE(FAIL, 'ingest_collectors is append-only'); END;

CREATE TRIGGER IF NOT EXISTS ingest_collectors_no_delete
    BEFORE DELETE ON ingest_collectors
    BEGIN SELECT RAISE(FAIL, 'ingest_collectors is append-only'); END;
"""

COLLECTORS_GENESIS = hashlib.sha256(b"ingest_collectors/genesis").hexdigest()


def _collector_payload(entry: Dict[str, Any]) -> str:
    """JSON representation for hashing. Order matters."""
    return json.dumps({
        "name": entry["name"],
        "token_hash": entry["token_hash"],
        "note": entry["note"],
        "created_at": entry["created_at"],
        "revoked_at": entry["revoked_at"],
        "prev_hash": entry["prev_hash"],
    }, sort_keys=True, separators=(",", ":"))


def _collector_hash(entry: Dict[str, Any]) -> str:
    """SHA-256 hash of the entry payload."""
    payload = _collector_payload(entry)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def mint_token() -> str:
    """Return a random 32-byte token in hex. Returned exactly once per enrollment."""
    return secrets.token_hex(TOKEN_SIZE_BYTES)


def token_digest(token: str) -> str:
    """SHA-256 of the token. This is what we store and check against."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@contextmanager
def _atomic(db_path: str):
    """Context manager for an atomic transaction."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init(db_path: str) -> None:
    """Initialize the ingest_collectors table if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(COLLECTOR_DDL)
        # executescript, not execute: sqlite3 refuses multiple statements in a
        # single execute() call ("You can only execute one statement at a time").
        conn.executescript(COLLECTOR_TRIGGERS)


def enroll_collector(db_path: str, name: str, note: str = "") -> Dict[str, Any]:
    """
    Enroll a new collector and return the bearer token exactly once.

    The token is returned here and never stored in plaintext. Only the SHA-256
    digest is stored, so a database copy yields no usable token. The token must
    be communicated to the collector operator at this moment; if it is lost,
    enrollment must be revoked and a new enrollment created.

    Args:
        db_path: path to axiom.db
        name: display name for the collector (e.g. "ns-detector-wayside-5")
        note: optional human note

    Returns:
        A dict with the token, collector ID, name, and metadata.

    Raises:
        ValueError if the name is empty, contains whitespace, contains "@",
        or is already enrolled (not revoked).
    """
    init(db_path)
    name = (name or "").strip()
    if not name:
        raise ValueError("a collector name is required")
    if "@" in name or any(c.isspace() for c in name):
        raise ValueError("a collector name may not contain whitespace or '@'")
    note = (note or "").strip()

    with _atomic(db_path) as conn:
        dup = conn.execute(
            "SELECT name FROM ingest_collectors WHERE name = ? AND revoked_at IS NULL",
            (name,)).fetchone()
        if dup is not None:
            raise ValueError("collector %r is already enrolled" % name)

        prev = conn.execute(
            "SELECT entry_hash FROM ingest_collectors ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev["entry_hash"] if prev else COLLECTORS_GENESIS

        token = mint_token()
        digest = token_digest(token)
        now = conn.execute("SELECT datetime('now') AS t").fetchone()["t"]

        entry = {
            "name": name,
            "token_hash": digest,
            "note": note,
            "created_at": now,
            "revoked_at": None,
            "prev_hash": prev_hash,
        }
        entry["entry_hash"] = _collector_hash(entry)

        cur = conn.execute(
            "INSERT INTO ingest_collectors "
            "(name, token_hash, note, created_at, revoked_at, prev_hash, entry_hash) "
            "VALUES (?,?,?,?,?,?,?)",
            (entry["name"], entry["token_hash"], entry["note"],
             entry["created_at"], None, entry["prev_hash"], entry["entry_hash"]))
        entry["id"] = cur.lastrowid

    return {
        "token": token,
        "id": entry["id"],
        "name": name,
        "created_at": entry["created_at"],
    }


def revoke_collector(db_path: str, name: str, note: str = "") -> Dict[str, Any]:
    """
    Revoke a collector enrollment.

    Appends a new row with revoked_at set. The original enrollment row is not
    touched. Tokens already issued continue to resolve - see the module
    docstring for why. Idempotent: revoking an already-revoked collector is
    not an error.

    Args:
        db_path: path to axiom.db
        name: collector name to revoke
        note: optional human note

    Returns:
        A dict with the revocation metadata.

    Raises:
        ValueError if the name is not currently enrolled.
    """
    init(db_path)
    name = (name or "").strip()
    note = (note or "").strip()

    with _atomic(db_path) as conn:
        live = conn.execute(
            "SELECT id FROM ingest_collectors WHERE name = ? AND revoked_at IS NULL",
            (name,)).fetchone()
        if live is None:
            # Idempotent: check if any row exists at all for this name
            any_row = conn.execute(
                "SELECT id FROM ingest_collectors WHERE name = ? LIMIT 1",
                (name,)).fetchone()
            if any_row is None:
                raise ValueError("collector %r is not currently enrolled" % name)
            return {"name": name, "revoked_at": None, "note": "already revoked"}

        prev = conn.execute(
            "SELECT entry_hash FROM ingest_collectors ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev["entry_hash"]

        now = conn.execute("SELECT datetime('now') AS t").fetchone()["t"]
        entry = {
            "name": name,
            "token_hash": "",
            "note": note,
            "created_at": now,
            "revoked_at": now,
            "prev_hash": prev_hash,
        }
        entry["entry_hash"] = _collector_hash(entry)

        conn.execute(
            "INSERT INTO ingest_collectors "
            "(name, token_hash, note, created_at, revoked_at, prev_hash, entry_hash) "
            "VALUES (?,?,?,?,?,?,?)",
            (entry["name"], entry["token_hash"], entry["note"],
             entry["created_at"], entry["revoked_at"], entry["prev_hash"],
             entry["entry_hash"]))

    return {
        "name": name,
        "revoked_at": now,
    }


def resolve_token(db_path: str, token: str) -> Dict[str, Any]:
    """
    Turn a bearer token into the collector it stands for, or raise ValueError.

    Unlike reviewer sessions, there is no TTL and no check for the token's
    own revocation - a revoked enrollment's issued tokens keep working. This is
    the deliberate difference between a machine credential and a human one.

    Args:
        db_path: path to axiom.db
        token: the bearer token string

    Returns:
        A dict with collector_id and collector_name.

    Raises:
        ValueError if the token is absent, malformed, or not recognised.
    """
    init(db_path)
    if not token:
        raise ValueError("no ingest token presented")

    try:
        digest = token_digest(token)
    except Exception as exc:
        raise ValueError("malformed ingest token: %s" % exc)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.execute(
            "SELECT id, name FROM ingest_collectors "
            "WHERE token_hash = ? AND revoked_at IS NULL",
            (digest,)).fetchone()
        if c is None:
            raise ValueError("ingest token is not recognised")

    return {"collector_id": c["id"], "collector_name": c["name"]}


def auth_mode(db_path: str) -> str:
    """
    Whether this deployment can accept ingest payloads at all.

    AUTH_NONE means no collector has been enrolled, so the ingest endpoint is
    closed (returns 503). AUTH_REQUIRED means at least one live enrollment
    exists.

    Returns:
        AUTH_NONE or AUTH_REQUIRED.
    """
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        n = conn.execute(
            "SELECT COUNT(*) AS n FROM ingest_collectors WHERE revoked_at IS NULL"
        ).fetchone()[0]
    return AUTH_REQUIRED if n else AUTH_NONE


def verify_chain(db_path: str) -> Dict[str, Any]:
    """
    Verify the collector enrollment chain.

    Returns a dict with 'ok' (bool) and 'message' (str). This is a
    tamper-evident check, not an authentication.
    """
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM ingest_collectors ORDER BY id ASC"
        ).fetchall()

    prev_hash = COLLECTORS_GENESIS
    for i, row in enumerate(rows):
        if row["prev_hash"] != prev_hash:
            return {
                "ok": False,
                "message": "chain break at record %d (id %d): expected prev_hash %s, "
                           "got %s" % (i, row["id"], prev_hash, row["prev_hash"]),
            }
        entry = {
            "name": row["name"],
            "token_hash": row["token_hash"],
            "note": row["note"],
            "created_at": row["created_at"],
            "revoked_at": row["revoked_at"],
            "prev_hash": row["prev_hash"],
        }
        expected_hash = _collector_hash(entry)
        if row["entry_hash"] != expected_hash:
            return {
                "ok": False,
                "message": "hash mismatch at record %d (id %d, name %r): expected "
                           "%s, got %s" % (i, row["id"], row["name"],
                                           expected_hash, row["entry_hash"]),
            }
        prev_hash = row["entry_hash"]

    return {"ok": True, "message": "chain verified (%d enrollments)" % len(rows)}


def enrollments(db_path: str) -> List[Dict[str, Any]]:
    """Return the full enrollment history, oldest first. Includes revoked entries."""
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name, note, created_at, revoked_at FROM ingest_collectors "
            "ORDER BY id ASC"
        ).fetchall()
    return [dict(r) for r in rows]
