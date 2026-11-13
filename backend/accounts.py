"""
Local accounts and authenticated sessions — the entry half of AD-2.

`attribution.py` makes a disposition *verifiable after the fact*: a registered
reviewer's key can attest a row, and a recipient of an export can tell which
registered identity attested it. It does not make a disposition *authenticated at
entry*. Until this module, `POST /api/warrant/<id>/disposition` accepted a
free-text `reviewer_name` and `cert_id` and wrote the row, so the name on a
decision was a claim, not a fact. B01 §7 item 1 has said so since chat-5.

**What this module adds.** An account is bound to a certification record that is
already in the reviewer registry. A reviewer signs in with a username and a
passphrase; the sign-in mints a short-lived bearer token; the disposition route
derives `reviewer_name` and `cert_id` from the token and refuses a request that
claims them in the body instead.

**What it still does not claim, and will not be made to claim.**

  * It does not prove a human was at the keyboard. It proves a usable credential
    was presented. Binding a credential to a person is issuance and personnel
    control — key custody and joiner/mover/leaver — which is a procedure, not a
    function in this file. B01 §7 item 1 keeps that half open by name.
  * It does not protect the token in transit. The demo host is plain HTTP and
    B01 §7 item 10 already says so; on the Railroad's isolated network the token
    still needs TLS or segment isolation, because a bearer token over plain HTTP
    is a shared secret handed to anyone on the wire.
  * It does not make the attestation stronger. A signed-in session authorises a
    *write*; the attestation that makes the decision exportable is still made by
    the reviewer's HMAC key, which the server never holds. See `attribution.py`.

**Why a passphrase and not the reviewer key itself.** Reusing the 32-byte HMAC
key as a login credential would put the attestation secret on the server for the
duration of every session, which converts "the server cannot forge attestations"
into "the server can forge attestations while a reviewer is logged in". The
account secret is separate, stored only as a PBKDF2 verifier, and cannot sign
anything.

**The token is never stored.** Only a SHA-256 digest of it is written to the
session table. A copy of the database therefore does not yield a usable token,
and revocation is by digest.

Schema note: the `sessions` table is *not* append-only in the ledger sense.
Revocation is an UPDATE of `revoked_at` on a session row, which is ordinary
lifecycle state rather than evidence — unlike the registry and the ledger, where
an edit would destroy the record. What is append-only is the account register:
an account cannot be rewritten or deleted, only revoked by a new entry, for the
same reason the reviewer registry is chained.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional

from . import attribution

# OWASP's 2023 floor for PBKDF2-HMAC-SHA256. High enough to be expensive to guess
# and low enough that a sign-in on the demo box stays under a second. Stored per
# account so the number can rise later without invalidating existing verifiers.
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16
TOKEN_BYTES = 32
DEFAULT_SESSION_TTL_SECONDS = 8 * 3600

# A sign-in attempt that fails this many times inside the window is refused for
# the rest of it. Deliberately simple and deliberately loud: on an air-gapped
# box with a handful of reviewers there is no legitimate reason for 10 failures
# in 15 minutes, and the refusal is logged so an operator sees it.
LOCKOUT_THRESHOLD = 10
LOCKOUT_WINDOW_SECONDS = 15 * 60

ACCOUNTS_GENESIS = "0" * 64

# What a deployment's disposition-entry policy is. The route asks before it
# reads a token, so the two modes are distinguishable in a response rather than
# by an inference about why a token was refused.
AUTH_REQUIRED = "required"   # accounts exist; a live session token is mandatory
AUTH_NONE = "none"           # no account enrolled; entry is closed, not open

ACCOUNTS_DDL = """
CREATE TABLE IF NOT EXISTS accounts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL,
    reviewer_name TEXT NOT NULL,
    cert_id       TEXT NOT NULL,
    key_id        TEXT NOT NULL,
    salt          TEXT NOT NULL,
    iterations    INTEGER NOT NULL,
    verifier      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    revoked_at    TEXT,
    note          TEXT NOT NULL DEFAULT '',
    prev_hash     TEXT NOT NULL,
    entry_hash    TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_username
ON accounts (username, id);

CREATE TABLE IF NOT EXISTS sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    issued_at  TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_account ON sessions (account_id, id);

CREATE TABLE IF NOT EXISTS auth_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    at         TEXT NOT NULL DEFAULT (datetime('now')),
    username   TEXT NOT NULL,
    outcome    TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events (username, at);

CREATE TRIGGER IF NOT EXISTS accounts_no_update
BEFORE UPDATE ON accounts
BEGIN
    SELECT RAISE(ABORT, 'account register is append-only: revocation is a new entry, not an edit');
END;

CREATE TRIGGER IF NOT EXISTS accounts_no_delete
BEFORE DELETE ON accounts
BEGIN
    SELECT RAISE(ABORT, 'account register is append-only: entries cannot be deleted');
END;

CREATE TRIGGER IF NOT EXISTS accounts_no_replace
BEFORE INSERT ON accounts
WHEN EXISTS (SELECT 1 FROM accounts WHERE id = NEW.id)
BEGIN
    SELECT RAISE(ABORT, 'account register is append-only: INSERT OR REPLACE over an existing entry is not permitted');
END;

CREATE TRIGGER IF NOT EXISTS auth_events_no_update
BEFORE UPDATE ON auth_events
BEGIN
    SELECT RAISE(ABORT, 'the authentication log is append-only');
END;

CREATE TRIGGER IF NOT EXISTS auth_events_no_delete
BEFORE DELETE ON auth_events
BEGIN
    SELECT RAISE(ABORT, 'the authentication log is append-only');
END;
"""


@contextmanager
def _atomic(db_path: str):
    # `timeout` is the connection-level wait; without it sqlite3 defaults to 5 s
    # and a second writer fails while the ledger's own connection would have
    # queued for 30 s. The ledger, the account register and the reviewer registry
    # share one file, so all three must agree on how long to wait or the one with
    # the short fuse errors first under contention.
    conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def init(db_path: str) -> None:
    attribution.init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(ACCOUNTS_DDL)


# ---------------------------------------------------------------------------
# Credential primitives (pure — no database, no state)
# ---------------------------------------------------------------------------
def derive_verifier(passphrase: str, salt: bytes,
                    iterations: int = PBKDF2_ITERATIONS) -> str:
    """
    PBKDF2-HMAC-SHA256 over the passphrase. Returns lowercase hex.

    Uses hashlib's own implementation. This product tells CISOs it does not
    hand-roll crypto, and a KDF written here would be the exception that
    disproves it.
    """
    if not isinstance(passphrase, str) or not passphrase:
        raise ValueError("a passphrase is required and cannot be empty")
    if not salt:
        raise ValueError("a salt is required; use new_salt() for account creation")
    if iterations < 1:
        raise ValueError("iterations must be positive")
    return hashlib.pbkdf2_hmac(
        "sha256", passphrase.encode("utf-8"), salt, iterations).hex()


def new_salt() -> bytes:
    """
    16 random bytes. The length policy lives here, at the only place a salt is
    made, rather than inside `derive_verifier`: that function is a thin wrapper
    over hashlib and must accept the published test vectors, which use a 4-byte
    salt. Validating there rejected the vectors and proved nothing about the
    accounts, which can only ever be created with `new_salt()`.
    """
    return secrets.token_bytes(SALT_BYTES)


def verify_passphrase(passphrase: str, salt_hex: str, iterations: int,
                      expected_hex: str) -> bool:
    """
    Constant-time check of a passphrase against a stored verifier.

    `hmac.compare_digest` rather than `==`: a string comparison that exits at
    the first differing byte is a byte-at-a-time oracle, and on a local network
    that is enough to walk a verifier out one character at a time.
    """
    try:
        salt = bytes.fromhex(salt_hex)
    except (TypeError, ValueError):
        return False
    try:
        got = derive_verifier(passphrase, salt, iterations)
    except ValueError:
        return False
    return hmac.compare_digest(got, expected_hex)


def mint_token() -> str:
    """A bearer token. Returned to the caller once and never stored in clear."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def token_digest(token: str) -> str:
    if not isinstance(token, str) or not token:
        raise ValueError("token must be a non-empty string")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Account register
# ---------------------------------------------------------------------------
def _account_payload(entry: Dict[str, object]) -> str:
    """
    What an account entry's hash covers.

    `salt`, `iterations` and `verifier` are in here on purpose. A host owner who
    could swap a verifier for one they know the passphrase to would own the
    account, and every session it ever issued. A value the hash does not cover
    is a value somebody can change.
    """
    return json.dumps(
        {k: entry[k] for k in ("username", "reviewer_name", "cert_id", "key_id",
                               "salt", "iterations", "verifier", "note",
                               "created_at", "revoked_at", "prev_hash")},
        sort_keys=True, separators=(",", ":"))


def _account_hash(entry: Dict[str, object]) -> str:
    return hashlib.sha256(_account_payload(entry).encode("utf-8")).hexdigest()


def _cert_is_live(db_path: str, cert_id: str, key_id: str) -> bool:
    """
    Is the certification still in force?

    **The newest registry entry for the pair is the one that counts.** Revocation
    appends a row carrying `revoked_at`; it does not edit the original, whose
    `revoked_at` therefore stays NULL forever. A predicate written as "some entry
    for this certificate has no revoked_at" is true for every revoked certificate
    and is how this function was first written and first failed — four tests, one
    cause (2026-11-11). The same shape as `_live_account`.
    """
    entries = [e for e in attribution.registry(db_path)
               if e["cert_id"] == cert_id and e["key_id"] == key_id]
    if not entries:
        return False
    return entries[-1]["revoked_at"] is None


def auth_mode(db_path: str) -> str:
    """
    Whether this deployment can accept a disposition at all.

    `AUTH_NONE` means no account has been enrolled, so **the write path is
    closed**. That is the deliberate part: the tempting alternative is to fall
    back to the old free-text behaviour when no account exists, so a fresh demo
    keeps working. Then the gate is only ever as strong as somebody remembering
    to enroll an account, and the first attacker to find an un-enrolled host gets
    the old route back. Fail closed.

    The cost is real and stated in B01 §7 item 1: the demo UI cannot record a
    decision on a fresh database until an account exists. A seeder exists for the
    demo — see `tools/seed_demo_account.py` — and it is a deliberate act.
    """
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        n = conn.execute(
            "SELECT COUNT(*) AS n FROM accounts WHERE revoked_at IS NULL"
        ).fetchone()["n"]
    return AUTH_REQUIRED if n else AUTH_NONE


def cert_is_live(db_path: str, cert_id: str, key_id: str) -> bool:
    """Public name for the liveness predicate the write guard needs."""
    return _cert_is_live(db_path, cert_id, key_id)


def enroll(db_path: str, username: str, passphrase: str, cert_id: str,
           note: str = "", iterations: int = PBKDF2_ITERATIONS) -> Dict[str, object]:
    """
    Create an account for a reviewer who already holds a live certification
    record in the reviewer registry.

    The binding runs one way and is enforced here: an account cannot be created
    for a certificate the registry does not have, so authentication cannot
    manufacture an identity that attribution would later refuse to attest. The
    reverse direction is checked at session resolve time, because a certificate
    can be revoked after the account is made.
    """
    init(db_path)
    username = (username or "").strip()
    if not username:
        raise ValueError("a username is required")
    if "@" in username or any(c.isspace() for c in username):
        raise ValueError("a username may not contain whitespace or '@'")
    cert_id = (cert_id or "").strip()
    if not cert_id:
        raise ValueError("a certification ID is required")

    live = [e for e in attribution.registry(db_path)
            if e["cert_id"] == cert_id and e["revoked_at"] is None]
    # The already-existing filter above is safe here only because it runs *before*
    # any revocation entry for this certificate can exist under a different
    # revoked_at; enroll still ends by asking `_cert_is_live` below, which is the
    # predicate that stays correct for the rest of the account's life.
    live = [e for e in live if _cert_is_live(db_path, e["cert_id"], e["key_id"])]
    if not live:
        raise ValueError(
            "certification %r is not in the reviewer registry, or has been "
            "revoked — an account is bound to an issued certificate, so issue "
            "one with attribution.register() first" % cert_id)
    entry0 = live[-1]

    salt = new_salt()
    verifier = derive_verifier(passphrase, salt, iterations)
    now = _now(db_path)

    with _atomic(db_path) as conn:
        dup = _live_account(conn, username)
        if dup is not None:
            raise ValueError("username %r is already in use" % username)
        prev = conn.execute(
            "SELECT entry_hash FROM accounts ORDER BY id DESC LIMIT 1").fetchone()
        prev_hash = prev["entry_hash"] if prev else ACCOUNTS_GENESIS
        entry = {
            "username": username,
            "reviewer_name": entry0["reviewer"],
            "cert_id": cert_id,
            "key_id": entry0["key_id"],
            "salt": salt.hex(),
            "iterations": int(iterations),
            "verifier": verifier,
            "note": note,
            "created_at": now,
            "revoked_at": None,
            "prev_hash": prev_hash,
        }
        entry["entry_hash"] = _account_hash(entry)
        cur = conn.execute(
            "INSERT INTO accounts (username, reviewer_name, cert_id, key_id, "
            "salt, iterations, verifier, note, created_at, revoked_at, "
            "prev_hash, entry_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (entry["username"], entry["reviewer_name"], entry["cert_id"],
             entry["key_id"], entry["salt"], entry["iterations"],
             entry["verifier"], entry["note"], entry["created_at"], None,
             entry["prev_hash"], entry["entry_hash"]))
        entry["id"] = cur.lastrowid
    # The verifier never leaves this function.
    entry.pop("verifier", None)
    entry.pop("salt", None)
    return dict(entry)


def revoke_account(db_path: str, username: str, note: str = "") -> Dict[str, object]:
    """
    Revoke every live account under `username` and, in the same transaction,
    every session they hold.

    Revocation is a new chained entry naming what changed, not an edit — the
    `revoked_at` on the original row is never touched, so the register still
    shows the account existed. Sessions are revoked here rather than left to
    expire because a revoked account whose live token still writes dispositions
    is exactly the failure the revocation was meant to prevent.
    """
    init(db_path)
    now = _now(db_path)
    with _atomic(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM accounts WHERE username = ? AND revoked_at IS NULL "
            "ORDER BY id", (username,)).fetchall()
        if not rows:
            raise ValueError("no live account named %r" % username)
        prev = conn.execute(
            "SELECT entry_hash FROM accounts ORDER BY id DESC LIMIT 1").fetchone()
        prev_hash = prev["entry_hash"] if prev else ACCOUNTS_GENESIS
        last = None
        for row in rows:
            entry = {
                "username": row["username"],
                "reviewer_name": row["reviewer_name"],
                "cert_id": row["cert_id"],
                "key_id": row["key_id"],
                "salt": row["salt"],
                "iterations": row["iterations"],
                "verifier": row["verifier"],
                "note": note or ("revoked: %s" % row["username"]),
                "created_at": row["created_at"],
                "revoked_at": now,
                "prev_hash": prev_hash,
            }
            # Append-only triggers refuse UPDATE, so revocation is a *new* row
            # carrying the same identity with `revoked_at` set. The unique index
            # is on (username, id), not username alone, so this is permitted and
            # `_live_account` picks the newest unrevoked row.
            entry["entry_hash"] = _account_hash(entry)
            cur = conn.execute(
                "INSERT INTO accounts (username, reviewer_name, cert_id, key_id, "
                "salt, iterations, verifier, note, created_at, revoked_at, "
                "prev_hash, entry_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (entry["username"], entry["reviewer_name"], entry["cert_id"],
                 entry["key_id"], entry["salt"], entry["iterations"],
                 entry["verifier"], entry["note"], entry["created_at"], now,
                 entry["prev_hash"], entry["entry_hash"]))
            prev_hash = entry["entry_hash"]
            last = dict(entry)
            last["id"] = cur.lastrowid
        conn.execute(
            "UPDATE sessions SET revoked_at = ? WHERE account_id IN ("
            "SELECT id FROM accounts WHERE username = ?) AND revoked_at IS NULL",
            (now, username))
    last.pop("verifier", None)
    last.pop("salt", None)
    return last


def _now(db_path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT datetime('now') AS t").fetchone()[0]


def _live_account(conn, username: str) -> Optional[Dict[str, object]]:
    """
    The account currently in force for `username`.

    Revocation appends a row with `revoked_at` set, so "live" means the newest
    row for the username has no `revoked_at`. A newest row that is revoked means
    the account is gone even though older live rows are still on disk — reading
    the oldest instead would resurrect a revoked account.
    """
    row = conn.execute(
        "SELECT * FROM accounts WHERE username = ? ORDER BY id DESC LIMIT 1",
        (username,)).fetchone()
    if row is None or row["revoked_at"] is not None:
        return None
    return dict(row)


def accounts(db_path: str) -> List[Dict[str, object]]:
    """Every account row, newest last. Verifiers and salts are withheld."""
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        out = []
        for r in conn.execute("SELECT * FROM accounts ORDER BY id"):
            d = dict(r)
            d.pop("verifier", None)
            d.pop("salt", None)
            out.append(d)
        return out


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def _record_event(db_path: str, username: str, outcome: str, detail: str = "") -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO auth_events (username, outcome, detail) VALUES (?,?,?)",
            (username, outcome, detail))


def _recent_failures(conn, username: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM auth_events WHERE username = ? "
        "AND outcome = 'failed' AND at > datetime('now', ?)",
        (username, "-%d seconds" % LOCKOUT_WINDOW_SECONDS)).fetchone()
    return int(row["n"])


def authenticate(db_path: str, username: str, passphrase: str) -> Dict[str, object]:
    """
    Check a passphrase and return the account, or raise ValueError with a reason
    that does not distinguish "no such user" from "wrong passphrase".

    That second property is deliberate: an error that says "no such username"
    turns the sign-in form into a user directory. The *log* distinguishes them,
    because an operator investigating a break-in needs to.
    """
    init(db_path)
    username = (username or "").strip()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if _recent_failures(conn, username) >= LOCKOUT_THRESHOLD:
            _record_event(db_path, username, "locked", "threshold reached")
            raise ValueError(
                "too many failed sign-in attempts for this account; try again "
                "after %d minutes or ask an administrator to clear the log"
                % (LOCKOUT_WINDOW_SECONDS // 60))
        acct = _live_account(conn, username)

    ok = False
    if acct is not None:
        ok = verify_passphrase(passphrase, acct["salt"], acct["iterations"],
                               acct["verifier"])
    if not ok:
        _record_event(db_path,
                      username,
                      "failed",
                      "no such account" if acct is None else "wrong passphrase")
        # Same message either way — see the docstring.
        raise ValueError("that username and passphrase do not match an account")
    _record_event(db_path, username, "signed_in")
    acct.pop("verifier", None)
    acct.pop("salt", None)
    return acct


def issue_session(db_path: str, username: str, passphrase: str,
                  ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS) -> Dict[str, object]:
    """
    Authenticate and mint a bearer token. The token is returned exactly once.

    The certification is re-checked here as well as at resolve time, because a
    sign-in is the last moment at which refusing costs the reviewer nothing.
    """
    if ttl_seconds <= 0:
        raise ValueError("a session must live longer than zero seconds")
    acct = authenticate(db_path, username, passphrase)

    if not _cert_is_live(db_path, acct["cert_id"], acct["key_id"]):
        _record_event(db_path, username, "refused", "certification revoked")
        raise ValueError(
            "the certification this account is bound to has been revoked; a "
            "revoked certificate cannot authorise a decision")

    token = mint_token()
    digest = token_digest(token)
    with _atomic(db_path) as conn:
        now = conn.execute("SELECT datetime('now') AS t").fetchone()["t"]
        expires = conn.execute(
            "SELECT datetime('now', ?) AS t", ("+%d seconds" % ttl_seconds,)
        ).fetchone()["t"]
        cur = conn.execute(
            "INSERT INTO sessions (token_hash, account_id, issued_at, expires_at) "
            "VALUES (?,?,?,?)", (digest, acct["id"], now, expires))
        sid = cur.lastrowid
    return {"token": token, "session_id": sid, "account_id": acct["id"],
            "username": acct["username"], "reviewer_name": acct["reviewer_name"],
            "cert_id": acct["cert_id"], "issued_at": now, "expires_at": expires}


def resolve_session(db_path: str, token: str) -> Dict[str, object]:
    """
    Turn a bearer token into the identity it stands for, or raise ValueError.

    Five things are checked and every one of them has caught something in review
    or is obviously load-bearing:

      1. the digest is in `sessions`            — the token was issued here;
      2. the session is not revoked             — sign-out and account revocation;
      3. the session has not expired            — TTL;
      4. the account is still live              — revocation appends a row;
      5. the certification is still live        — revoked or reissued since sign-in.

    Check 5 is the one that is easy to leave out and expensive to leave out. A
    reviewer whose certificate is revoked at 09:00 with a session issued at 08:00
    would otherwise keep writing decisions until the TTL ran out, and each one
    would be attributable to a certificate that no longer exists.
    """
    init(db_path)
    if not token:
        raise ValueError("no session token presented")
    try:
        digest = token_digest(token)
    except ValueError:
        raise ValueError("malformed session token")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        s = conn.execute("SELECT * FROM sessions WHERE token_hash = ?",
                         (digest,)).fetchone()
        if s is None:
            raise ValueError("session token is not recognised")
        if s["revoked_at"] is not None:
            raise ValueError("this session was revoked at %s" % s["revoked_at"])
        expired = conn.execute(
            "SELECT (? <= datetime('now')) AS v", (s["expires_at"],)).fetchone()["v"]
        if expired:
            raise ValueError("this session expired at %s" % s["expires_at"])
        acct = _live_account_by_id(conn, s["account_id"])
        if acct is None:
            raise ValueError("the account behind this session has been revoked")

    if not _cert_is_live(db_path, acct["cert_id"], acct["key_id"]):
        raise ValueError(
            "the certification behind this session has been revoked; sign in "
            "again once a current certificate is issued")

    return {"session_id": s["id"], "account_id": acct["id"],
            "username": acct["username"], "reviewer_name": acct["reviewer_name"],
            "cert_id": acct["cert_id"], "key_id": acct["key_id"],
            "issued_at": s["issued_at"], "expires_at": s["expires_at"]}


def _live_account_by_id(conn, account_id: int) -> Optional[Dict[str, object]]:
    """
    The account in force for the username that owned account row `account_id`.

    Revocation appends a new row for the same username, so the session's original
    row is still present and still says `revoked_at IS NULL` — checking that row
    alone would let a revoked account's sessions keep working. The live row is
    the newest for the username.
    """
    orig = conn.execute("SELECT username FROM accounts WHERE id = ?",
                        (account_id,)).fetchone()
    if orig is None:
        return None
    return _live_account(conn, orig["username"])


def revoke_session(db_path: str, token: str) -> Dict[str, object]:
    """Sign out. Idempotent: revoking an already-revoked session is not an error."""
    init(db_path)
    digest = token_digest(token)
    with _atomic(db_path) as conn:
        row = conn.execute("SELECT * FROM sessions WHERE token_hash = ?",
                           (digest,)).fetchone()
        if row is None:
            raise ValueError("session token is not recognised")
        if row["revoked_at"] is None:
            conn.execute(
                "UPDATE sessions SET revoked_at = datetime('now') WHERE id = ?",
                (row["id"],))
        return {"session_id": row["id"], "revoked": True}


def verify_accounts(db_path: str) -> Dict[str, object]:
    """
    Recompute the account register's hash chain. Returns a report, never raises
    on a broken chain — a reader needs the detail, and a verifier that throws
    cannot tell you which entry moved.
    """
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT * FROM accounts ORDER BY id")]
    prev = ACCOUNTS_GENESIS
    problems = []
    for r in rows:
        if r["prev_hash"] != prev:
            problems.append({"id": r["id"], "problem": "prev_hash does not match "
                             "the preceding entry's entry_hash"})
        recomputed = _account_hash({
            "username": r["username"], "reviewer_name": r["reviewer_name"],
            "cert_id": r["cert_id"], "key_id": r["key_id"], "salt": r["salt"],
            "iterations": r["iterations"], "verifier": r["verifier"],
            "note": r["note"], "created_at": r["created_at"],
            "revoked_at": r["revoked_at"], "prev_hash": r["prev_hash"]})
        if recomputed != r["entry_hash"]:
            problems.append({"id": r["id"],
                             "problem": "entry content does not hash to entry_hash"})
        prev = r["entry_hash"]
    return {"ok": not problems, "entries": len(rows), "problems": problems}
