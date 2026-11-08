"""
SQLite-backed persistence for reviewer dispositions.

Deliberately the stdlib `sqlite3` module -- no new dependency, no server
process, one file (`axiom.db`) that lives next to the app and survives a
restart. This replaces an earlier in-memory dict: a disposition is an
audit-relevant record (who reviewed what, and what they decided), and
losing it on every restart undercuts the whole "human-in-the-loop" story.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, Optional

DB_PATH = os.environ.get("AXIOM_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "axiom.db"))


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dispositions (
                advisory_id TEXT PRIMARY KEY,
                reviewer_name TEXT NOT NULL,
                cert_id TEXT NOT NULL,
                disposition TEXT NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def save_disposition(advisory_id: str, reviewer_name: str, cert_id: str, disposition: str):
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO dispositions (advisory_id, reviewer_name, cert_id, disposition, recorded_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(advisory_id) DO UPDATE SET
                reviewer_name=excluded.reviewer_name,
                cert_id=excluded.cert_id,
                disposition=excluded.disposition,
                recorded_at=excluded.recorded_at
            """,
            (advisory_id, reviewer_name, cert_id, disposition),
        )


def get_disposition(advisory_id: str) -> Optional[Dict[str, str]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT reviewer_name, cert_id, disposition, recorded_at FROM dispositions WHERE advisory_id = ?",
            (advisory_id,),
        ).fetchone()
    if row is None:
        return None
    return {"reviewer_name": row[0], "cert_id": row[1], "disposition": row[2], "recorded_at": row[3]}


def all_dispositions() -> Dict[str, Dict[str, str]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT advisory_id, reviewer_name, cert_id, disposition, recorded_at FROM dispositions"
        ).fetchall()
    return {
        r[0]: {"reviewer_name": r[1], "cert_id": r[2], "disposition": r[3], "recorded_at": r[4]}
        for r in rows
    }
