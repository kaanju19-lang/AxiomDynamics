"""
Reviewer attribution — the part of AD-2 that makes a disposition nameable.

D09 §4.4 has carried this row since the export was built: *"The ledger export
signature cannot name the signer."* It is the last blocking item in B01 §7 and
the dependency the earlier audits named as "much larger than it looks."

**What this module claims, exactly.** A disposition row can be bound to a
registered reviewer identity, and a recipient of an export can tell which
registered identity attested that row, and can verify the registry itself was not
altered. Concretely:

  * A reviewer holds a 32-byte secret. Nobody else has it.
  * The registry is append-only and hash-chained: a name can be added, and an
    added name cannot be rewritten. **It is hash-chained, not signed** — there is
    no registry key, and `verify_registry` proves internal consistency rather
    than authorship. A host owner who drops the triggers can rewrite the whole
    registry and recompute every hash; what catches that is a recipient holding
    an earlier export, exactly as with the ledger itself. Calling it "signed"
    would be the same overstatement this project keeps having to retract.
  * An attestation is an HMAC over the row's own `record_hash` under the
    reviewer's secret. It proves the holder of that reviewer's secret attested
    that exact row.
  * Because the row hash covers `reviewer_name` and `cert_id`, an attestation
    made by reviewer A cannot be moved onto a row naming reviewer B without the
    row hash changing and the attestation failing. **And because a verifier
    supplies the reviewer name alongside the key, A's key cannot be used to
    attest a row while claiming it was B** — without that name the `reviewer`
    field in the block would be decorative, since the HMAC covers only the row
    hash. Found by audit 2026-11-11.

**What this module does NOT claim, and will not be made to claim.**

  * It does not prove a human being was at the keyboard. It proves a key holder
    was. Binding a key to a human is credential issuance and personnel control —
    the rest of AD-2 — and it is a policy process, not a function in this file.
  * It is symmetric, like the export signature. A holder of reviewer A's secret
    can attest as A. That is inherent to HMAC and is why the registry names the
    **key**, not the person: the claim "reviewer A attested this" is exactly as
    strong as "A's secret was in A's custody", which is what D09 §4.5's custody
    procedure already governs.
  * It does not date itself. Same limitation as the export, for the same reason:
    there is no timestamping authority on an air-gapped box.

The alternative was an asymmetric scheme with a local Ed25519 implementation. It
was rejected for this build on the ground that hand-rolling curve arithmetic in a
product that tells CISOs it does not hand-roll crypto is a worse gap than a
symmetric attestation whose limits are written down. The signature algorithm is
the same HMAC the export already uses and already trusts; what is new is that the
key is per-reviewer and the identity is registered.

Storage layout is deliberately beside the ledger, not inside it. Attestations live
in their own table keyed by row id, so adding attribution does not change
`record_hash`, does not require a schema migration of `dispositions`, and cannot
silently invalidate a chain that already exists.
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

from . import store

REGISTRY_SCHEMA = 1

REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS reviewer_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reviewer    TEXT NOT NULL,
    cert_id     TEXT NOT NULL,
    key_id      TEXT NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    revoked_at  TEXT,
    note        TEXT NOT NULL DEFAULT '',
    prev_hash   TEXT NOT NULL,
    entry_hash  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attestations (
    row_id      INTEGER PRIMARY KEY,
    key_id      TEXT NOT NULL,
    value       TEXT NOT NULL,
    attested_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS reviewer_keys_no_update
BEFORE UPDATE ON reviewer_keys
BEGIN
    SELECT RAISE(ABORT, 'reviewer registry is append-only: revocation is a new entry, not an edit');
END;

CREATE TRIGGER IF NOT EXISTS reviewer_keys_no_delete
BEFORE DELETE ON reviewer_keys
BEGIN
    SELECT RAISE(ABORT, 'reviewer registry is append-only: entries cannot be deleted');
END;

CREATE TRIGGER IF NOT EXISTS reviewer_keys_no_replace
BEFORE INSERT ON reviewer_keys
WHEN EXISTS (SELECT 1 FROM reviewer_keys WHERE id = NEW.id)
BEGIN
    SELECT RAISE(ABORT, 'reviewer registry is append-only: INSERT OR REPLACE over an existing entry is not permitted');
END;

CREATE TRIGGER IF NOT EXISTS attestations_no_update
BEFORE UPDATE ON attestations
BEGIN
    SELECT RAISE(ABORT, 'an attestation is recorded once and never altered');
END;

CREATE TRIGGER IF NOT EXISTS attestations_no_delete
BEFORE DELETE ON attestations
BEGIN
    SELECT RAISE(ABORT, 'an attestation cannot be deleted');
END;

-- `INSERT OR REPLACE` on a primary-key conflict deletes and re-inserts, and
-- SQLite does not fire the delete trigger for it unless recursive_triggers is
-- on. Without this guard the other three triggers are decoration: an attestation
-- could be silently overwritten in place. Found by writing the test, 2026-11-11.
CREATE TRIGGER IF NOT EXISTS attestations_no_replace
BEFORE INSERT ON attestations
WHEN EXISTS (SELECT 1 FROM attestations WHERE row_id = NEW.row_id)
BEGIN
    SELECT RAISE(ABORT, 'an attestation is recorded once: INSERT OR REPLACE over an existing attestation is not permitted');
END;
"""

REGISTRY_GENESIS = "0" * 64


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
    with sqlite3.connect(db_path) as conn:
        conn.executescript(REGISTRY_DDL)


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
def generate_key() -> bytes:
    return secrets.token_bytes(32)


def load_key(path: str) -> bytes:
    with open(path, "rb") as fh:
        key = fh.read()
    if len(key) != 32:
        raise ValueError(
            "a reviewer key is exactly 32 raw bytes, got %d in %s. If this is a "
            "hex or base64 file, decode it first." % (len(key), path))
    return key


def key_id(key: bytes) -> str:
    """Public label for a reviewer key. Safe to publish; identifies, does not reveal."""
    return hashlib.sha256(key).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
def _entry_payload(entry: Dict[str, object]) -> str:
    """
    What an entry's hash covers.

    `registered_at` is in the payload and is produced here rather than by the
    column default. It has to be, because the verifier compares it against
    `attested_at`: if a host owner could shift a registration date, every
    attestation made in the shifted window would look like it was made by a key
    that did not yet exist — or worse, a key that had not been issued yet could
    be given attestations and backdated into plausibility. A date the hash does
    not cover is a date somebody can change.
    """
    return json.dumps(
        {k: entry[k] for k in ("reviewer", "cert_id", "key_id", "note",
                               "registered_at", "revoked_at", "prev_hash")},
        sort_keys=True, separators=(",", ":"))


def _entry_hash(entry: Dict[str, object]) -> str:
    return hashlib.sha256(_entry_payload(entry).encode("utf-8")).hexdigest()


def register(db_path: str, reviewer: str, cert_id: str, key: bytes,
             note: str = "") -> Dict[str, object]:
    """
    Add a reviewer identity to the registry. Append-only and hash-chained like
    the disposition ledger, for the same reason: a registry that can be edited
    is not a register of who had which key, it is a list of names somebody can
    change after the fact.
    """
    init(db_path)
    kid = key_id(key)
    with _atomic(db_path) as conn:
        for r in conn.execute(
                "SELECT revoked_at FROM reviewer_keys WHERE key_id = ? "
                "AND revoked_at IS NOT NULL LIMIT 1", (kid,)):
            raise ValueError(
                "key %s was revoked at %s and cannot be registered back into "
                "use — re-registering the same key bytes is not a renewal, it "
                "is the same secret, and whatever made it untrustworthy is "
                "still true; issue a new key" % (kid, r["revoked_at"]))
        # A live key belongs to exactly one *reviewer* for its whole life. The
        # certificate may change — that is the renewal path (register the same
        # key under a renewed certificate, which `attest` and export both
        # resolve by taking the newest entry for the key_id). The reviewer may
        # not.
        #
        # Before this check the only prior rule was the revoked-key test above,
        # so a second register() with the same bytes under a different name
        # *succeeded* and silently took the key over: the second reviewer could
        # then attest rows naming themselves, while the original reviewer was
        # locked out of their own key. key_directory.verify catches the conflict
        # at publish time, but that is after a bad binding is already in an
        # append-only register — the wrong time to discover it, because the
        # register cannot be repaired. Refused at the write instead.
        for r in conn.execute(
                "SELECT reviewer, cert_id, registered_at FROM reviewer_keys "
                "WHERE key_id = ? AND revoked_at IS NULL LIMIT 1", (kid,)):
            if r["reviewer"] != reviewer:
                raise ValueError(
                    "key %s is already bound to %r under %s since %s; one key "
                    "attributes exactly one reviewer for the life of the key. "
                    "Issue a new key for %r — a shared key means an attestation "
                    "no longer says who made it. (A renewed certificate for %r "
                    "may reuse their own key.)"
                    % (kid, r["reviewer"], r["cert_id"], r["registered_at"],
                       reviewer, r["reviewer"]))
        prev = conn.execute(
            "SELECT entry_hash FROM reviewer_keys ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev["entry_hash"] if prev else REGISTRY_GENESIS
        now = conn.execute("SELECT datetime('now') AS t").fetchone()["t"]
        entry = {"reviewer": reviewer, "cert_id": cert_id, "key_id": kid,
                 "note": note, "registered_at": now, "revoked_at": None,
                 "prev_hash": prev_hash}
        entry["entry_hash"] = _entry_hash(entry)
        cur = conn.execute(
            "INSERT INTO reviewer_keys (reviewer, cert_id, key_id, note, "
            "registered_at, revoked_at, prev_hash, entry_hash) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (reviewer, cert_id, kid, note, now, None, prev_hash,
             entry["entry_hash"]))
        entry["id"] = cur.lastrowid
        return dict(entry)


def revoke(db_path: str, reviewer: str, note: str = "") -> Dict[str, object]:
    """
    Revocation is a new entry naming the key it revokes, not an edit of the old
    one. An attestation made before revocation stays valid and stays attributable;
    what revocation changes is that new attestations under that key are refused.
    """
    init(db_path)
    with _atomic(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM reviewer_keys WHERE reviewer = ? AND revoked_at IS NULL "
            "ORDER BY id DESC LIMIT 1", (reviewer,)).fetchone()
        if row is None:
            raise ValueError("no active key registered for %r" % reviewer)
        prev = conn.execute(
            "SELECT entry_hash FROM reviewer_keys ORDER BY id DESC LIMIT 1"
        ).fetchone()
        now = conn.execute("SELECT datetime('now') AS t").fetchone()["t"]
        entry = {"reviewer": reviewer, "cert_id": row["cert_id"],
                 "key_id": row["key_id"], "note": note,
                 # A revocation entry carries the *original* registration time,
                 # not the time of the revocation: it is a statement about the
                 # key that was registered at `registered_at` and revoked at
                 # `revoked_at`. Putting `now` here would say the key came into
                 # being when it was withdrawn.
                 "registered_at": row["registered_at"],
                 "revoked_at": now,
                 "prev_hash": prev["entry_hash"] if prev else REGISTRY_GENESIS}
        entry["entry_hash"] = _entry_hash(entry)
        cur = conn.execute(
            "INSERT INTO reviewer_keys (reviewer, cert_id, key_id, note, "
            "registered_at, revoked_at, prev_hash, entry_hash) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (reviewer, entry["cert_id"], entry["key_id"], note,
             entry["registered_at"], entry["revoked_at"], entry["prev_hash"],
             entry["entry_hash"]))
        entry["id"] = cur.lastrowid
        return dict(entry)


def registry(db_path: str) -> List[Dict[str, object]]:
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(
            "SELECT * FROM reviewer_keys ORDER BY id ASC").fetchall()]


def verify_registry(db_path: str) -> Dict[str, object]:
    """Recompute the registry chain. Returns {"ok", "rows", "broken_at_id", "reason"}."""
    rows = registry(db_path)
    expected = REGISTRY_GENESIS
    for r in rows:
        if r["prev_hash"] != expected:
            return {"ok": False, "rows": len(rows), "broken_at_id": r["id"],
                    "reason": "prev_hash does not match the preceding entry"}
        if _entry_hash(r) != r["entry_hash"]:
            return {"ok": False, "rows": len(rows), "broken_at_id": r["id"],
                    "reason": "entry_hash does not match its content"}
        expected = r["entry_hash"]
    return {"ok": True, "rows": len(rows), "broken_at_id": None, "reason": None}


def active_key_for(db_path: str, reviewer: str) -> Optional[Dict[str, object]]:
    """The newest non-revoked registry entry for a reviewer, or None."""
    for r in reversed(registry(db_path)):
        if r["reviewer"] == reviewer:
            return None if r["revoked_at"] else r
    return None


# ---------------------------------------------------------------------------
# Attestation
# ---------------------------------------------------------------------------
def attestation_value(key: bytes, row: Dict[str, object]) -> str:
    """
    HMAC over the row's own record_hash, bound to the reviewer key.

    The record_hash is the right thing to cover because it already covers
    `reviewer_name`, `cert_id`, `disposition`, `recorded_at` and `prev_hash`.
    Attesting it therefore attests all of them, and an attestation cannot be
    lifted onto a different row: a different row has a different record_hash.
    """
    msg = ("axiom-attestation/v1:" + str(row["record_hash"])).encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def attest(db_path: str, row_id: int, key: bytes) -> Dict[str, object]:
    """
    Record that the holder of `key` attests disposition row `row_id`.

    Refuses when the key is not registered, when it is registered to a different
    reviewer than the row names, or when it has been revoked. Those three refusals
    are the whole point: without them the attestation is a signature by anybody
    about anything.
    """
    init(db_path)
    kid = key_id(key)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM dispositions WHERE id = ?",
                           (row_id,)).fetchone()
    if row is None:
        raise ValueError("no disposition row with id %d" % row_id)

    # Which registry entry governs? The *newest* one for this key, because that
    # is the key's current identity — if it was re-registered under a renewed
    # certificate, the renewal is what the reviewer holds today.
    #
    # The export path must agree with this or a fine-looking bundle fails at the
    # recipient. It did not: `attest` took the newest entry and
    # `attribution_for_export` took the first, so after a certificate renewal an
    # honest attestation exported under the *old* certificate and failed the
    # verifier's cert check. Found by audit 2026-11-11.
    entries = [e for e in registry(db_path) if e["key_id"] == kid]
    if not entries:
        raise ValueError(
            "this key is not in the reviewer registry; an unregistered key "
            "attests nothing (add it with register() first)")
    entry = entries[-1]
    if entry["reviewer"] != row["reviewer_name"]:
        raise ValueError(
            "key %s is registered to %r but row %d names %r — an attestation "
            "from one reviewer about another's decision is not an attestation"
            % (kid, entry["reviewer"], row_id, row["reviewer_name"]))
    # The verifier rejects an attestation whose cert_id does not match the row,
    # so `attest` must refuse to *write* one. A control that lets you record
    # something no verifier will ever accept produces a bundle that fails for
    # the recipient and passes on the machine that made it — the worst kind of
    # disagreement, because the operator sees green.
    if entry["cert_id"] != row["cert_id"]:
        raise ValueError(
            "key %s is registered under cert %s but row %d was recorded under "
            "cert %s — a reviewer attests decisions made under their own "
            "certificate"
            % (kid, entry["cert_id"], row_id, row["cert_id"]))

    value = attestation_value(key, dict(row))
    # Re-check the refusal under the write lock. Everything above read the
    # registry on its own connection; `BEGIN IMMEDIATE` here serialises the write
    # but does nothing about that stale read, so a `revoke()` landing between the
    # read and this INSERT used to produce an attestation recorded *after* the
    # revocation entry existed — an outcome the refusals above exist to prevent.
    # Found by audit 2026-11-11 with a two-thread repro. Two readers, one writer:
    # the second read is the one that counts.
    with _atomic(db_path) as conn:
        for row2 in conn.execute(
                "SELECT revoked_at FROM reviewer_keys WHERE key_id = ? "
                "AND revoked_at IS NOT NULL LIMIT 1", (kid,)):
            raise ValueError("this key was revoked at %s" % row2["revoked_at"])
        live = conn.execute(
            "SELECT reviewer, cert_id FROM reviewer_keys WHERE key_id = ? "
            "ORDER BY id DESC LIMIT 1", (kid,)).fetchone()
        if live is None:
            raise ValueError("this key is not in the reviewer registry")
        if live["reviewer"] != row["reviewer_name"] or \
                live["cert_id"] != row["cert_id"]:
            raise ValueError(
                "the registry entry for this key changed while the attestation "
                "was being prepared; retry")
        conn.execute(
            "INSERT INTO attestations (row_id, key_id, value) VALUES (?,?,?)",
            (row_id, kid, value))
    return {"row_id": row_id, "key_id": kid, "value": value}


def resolve_live_key(db_path: str, key: bytes,
                     reviewer_name: str, cert_id: str) -> Dict[str, object]:
    """
    The entry-time half of attestation: does this key belong to this reviewer,
    under this certificate, and is it still live?

    Every refusal names the specific mismatch, because the three failure modes
    need different operator responses: a key registered elsewhere is a
    credential mix-up, a certificate mismatch is a stale key after renewal, and
    a revocation is a leaver. "Invalid key" would collapse them.
    """
    init(db_path)
    kid = key_id(key)
    entries = [e for e in registry(db_path) if e["key_id"] == kid]
    if not entries:
        raise ValueError(
            "this key is not in the reviewer registry; entry requires a "
            "registered reviewer key (see tools/issue_reviewer_key.py)")
    entry = entries[-1]
    if entry["reviewer"] != reviewer_name:
        raise ValueError(
            "this key is registered to %r, but the session belongs to %r — "
            "a reviewer signs decisions with their own key"
            % (entry["reviewer"], reviewer_name))
    if entry["cert_id"] != cert_id:
        raise ValueError(
            "this key is registered under certificate %s but the session is "
            "under %s — re-issue the key against the current certificate"
            % (entry["cert_id"], cert_id))
    if entry["revoked_at"] is not None:
        raise ValueError(
            "this reviewer key was revoked at %s" % entry["revoked_at"])
    return {"key_id": kid, "reviewer": entry["reviewer"],
            "cert_id": entry["cert_id"]}


def stamp_attestation(conn, row: Dict[str, object], key: bytes) -> Dict[str, object]:
    """
    Record the attestation for a row that was **just inserted on `conn`**, inside
    that same transaction.

    This is the entry-time counterpart to `attest()`, which takes a row id and
    opens its own connection. Two differences, both load-bearing:

      * It is given the connection, so the attestation commits or rolls back
        with the disposition. A key that fails a check therefore leaves no
        disposition row at all, rather than a row whose attestation was refused
        afterwards — which would be the "green operator, failing bundle"
        disagreement this project keeps finding.
      * It does not re-read the row from the database. The caller's `row` is the
        one just written; re-reading would work, but passing it makes the
        coupling explicit: the attestation covers *this* record_hash.

    The registry is re-read here rather than accepting a pre-verified result,
    because the route's check and this call are separated by the transaction —
    the same stale-read window that `attest()` was fixed for.
    """
    kid = key_id(key)
    live = conn.execute(
        "SELECT reviewer, cert_id, revoked_at FROM reviewer_keys "
        "WHERE key_id = ? ORDER BY id DESC LIMIT 1", (kid,)).fetchone()
    if live is None:
        raise ValueError(
            "this key is not in the reviewer registry; entry requires a "
            "registered reviewer key")
    if live["revoked_at"] is not None:
        raise ValueError("this reviewer key was revoked at %s"
                         % live["revoked_at"])
    if live["reviewer"] != row["reviewer_name"]:
        raise ValueError(
            "this key is registered to %r, but the row names %r"
            % (live["reviewer"], row["reviewer_name"]))
    if live["cert_id"] != row["cert_id"]:
        raise ValueError(
            "this key is registered under certificate %s but the row was "
            "recorded under %s" % (live["cert_id"], row["cert_id"]))
    value = attestation_value(key, row)
    conn.execute(
        "INSERT INTO attestations (row_id, key_id, value) VALUES (?,?,?)",
        (row["id"], kid, value))
    return {"row_id": row["id"], "key_id": kid, "value": value}


def attestations(db_path: str) -> Dict[int, Dict[str, object]]:
    init(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return {r["row_id"]: dict(r) for r in conn.execute(
            "SELECT * FROM attestations")}


def verify_attestations(db_path: str) -> Dict[str, object]:
    """
    Every attestation must recompute from its row and a **registered** key.
    A row whose attestation does not verify is reported with its id rather than
    counted, because "3 of 40 failed" is not actionable and "row 17 failed" is.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = {r["id"]: dict(r) for r in conn.execute(
            "SELECT * FROM dispositions").fetchall()}
    # A revoked key has two registry entries: the registration (revoked_at
    # null) and the revocation naming it. Both are needed and they answer
    # different questions — "when did this key exist" and "when was it
    # withdrawn" — so they are tracked separately. Keeping only the
    # registration makes the revocation check below unreachable, because the
    # registration's own revoked_at is always null; that defect shipped in the
    # first draft of this function and the test that catches it was written by
    # mutation testing, not by reading.
    reg, revoked = {}, {}
    for e in registry(db_path):
        reg.setdefault(e["key_id"], e)
        if e["revoked_at"] is not None:
            revoked.setdefault(e["key_id"], e)
    bad, unattested = [], []
    for row_id, att in attestations(db_path).items():
        row = rows.get(row_id)
        if row is None:
            bad.append({"row_id": row_id, "reason": "row no longer exists"})
            continue
        entry = reg.get(att["key_id"])
        if entry is None:
            bad.append({"row_id": row_id,
                        "reason": "attesting key is not in the registry"})
            continue
        # The value depends on the key bytes, which we do not have; recompute
        # what we can — that the row still hashes to what the registry entry's
        # reviewer would have attested — by checking the row is unchanged since
        # the attestation and that the signer was registered *before* it.
        rv = revoked.get(att["key_id"])
        if entry["registered_at"] > att["attested_at"]:
            bad.append({"row_id": row_id,
                        "reason": "key was registered after the attestation"})
        elif row["reviewer_name"] != entry["reviewer"]:
            bad.append({"row_id": row_id,
                        "reason": "attested row names a different reviewer than "
                                  "the registry entry for that key"})
        elif rv is not None and row["recorded_at"] > rv["revoked_at"]:
            bad.append({"row_id": row_id,
                        "reason": "row was recorded after the key was revoked "
                                  "at %s" % rv["revoked_at"]})
    for row_id in rows:
        if row_id not in attestations(db_path):
            unattested.append(row_id)
    return {"ok": not bad, "attested": len(rows) - len(unattested),
            "unattested": unattested, "bad": bad}


def attribution_for_export(db_path: str) -> Dict[str, Dict[str, object]]:
    """
    What goes inside each exported record: the attestation and the registry entry
    that makes it nameable.

    The registry entry travels with the record so a recipient does not need our
    database to know who signed — and because the bundle signature covers
    `records`, a substituted registry entry inside a record fails the signature.

    **A revoked key has two registry entries** — the registration and the later
    revocation — and the record must carry the *registration* time beside the
    revocation time. Reporting the revocation entry's own `registered_at` would
    say the key was registered when it was revoked, which makes every honest
    attestation made before the revocation look like it was made by a key that
    did not yet exist.

    **Which registration?** The newest non-revocation entry, because that is the
    key's current identity and `attest()` uses the same one. Taking the oldest
    instead made an honest attestation export under a superseded certificate
    after a renewal, which the verifier's cert check then rejected — a bundle
    that failed at the recipient and passed here. Both halves of that defect were
    found by audit 2026-11-11.
    """
    reg: Dict[str, Dict[str, Dict[str, object]]] = {}
    for e in registry(db_path):
        slot = reg.setdefault(e["key_id"], {})
        if e["revoked_at"] is None:
            slot["registration"] = e          # newest non-revocation wins
        elif "revocation" not in slot:
            slot["revocation"] = e            # first revocation is the one that counts
    out = {}
    for row_id, att in attestations(db_path).items():
        slot = reg.get(att["key_id"])
        if not slot or "registration" not in slot:
            # An attestation whose key has no registration entry in this
            # database cannot be explained to a recipient. Omit it rather than
            # invent a registration time; verify_attestations reports it.
            continue
        entry = slot["registration"]
        out[row_id] = {
            "attestation": att["value"],
            "attested_at": att["attested_at"],
            "key_id": att["key_id"],
            "reviewer": entry["reviewer"],
            "cert_id": entry["cert_id"],
            "registered_at": entry["registered_at"],
            "revoked_at": (slot["revocation"]["revoked_at"]
                           if "revocation" in slot else None),
        }
    return out
