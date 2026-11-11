"""
Signed, verifiable export of the disposition ledger (AD-3, part two).

`store.verify_chain()` proves the ledger is internally consistent *right now*.
That is not enough for the claim the docket needs to make: a party holding the
database file can drop the guard triggers, rewrite rows and recompute every
hash, and a verifier running on that same host would report a perfect chain.
Nor does a chain survive the disk.

This module produces a **bundle**: a bounded slice of the ledger, in canonical
form, with a count, an id range, the chain head, and an HMAC-SHA256 signature
over the whole thing. A third party holding the bundle and the key can verify
it without the database, without the exporting host, and without this code —
`tools/verify_ledger_export.py` re-implements the arithmetic from the spec in
about 150 lines of stdlib and imports nothing from `backend/`.

## What the signature is

**HMAC-SHA256, symmetric.** The stdlib has no Ed25519 and this project does not
hand-roll cryptography, so the honest choice is the symmetric one and an honest
statement of its limits. They are real:

- **Whoever can verify can forge.** An HMAC proves the bundle was produced by
  someone holding the key. It does not prove *which* party, because every
  verifier is also a signer. An asymmetric signature would separate those roles;
  it needs a library this deployment does not have.
- **It proves nothing about time.** There is no timestamping authority on an
  air-gapped box. A key holder can sign a bundle dated last year today. What
  protects against that is *custody*, not crypto: a regulator who receives
  bundles at intervals and keeps them can detect that a later bundle fails to
  extend an earlier one. `previous_export_hash` exists for exactly that.
- **The trust anchor is key distribution**, and that is AD-2 — the signed
  certification registry, still unbuilt (B01 §7 item 1). Until it exists, the
  key's provenance is a written procedure, not a cryptographic fact.

So the claim this supports is: *"the bundle you hold is byte-identical to the
bundle that was signed, no record inside it has been altered, and no record
within its stated range is missing."* It does not support: *"the ledger was
never rewritten before export"* or *"this bundle was created at the time it
claims."* Both remain open under D09 §4.4.

## What the verifier must check, and what `id` does not cover

The row hash covers `advisory_id, reviewer_name, cert_id, disposition, note,
recorded_at, supersedes_id, prev_hash` — **not `id`**. A row's `id` is outside
its hash. Swapping two ids inside a bundle therefore leaves every row hash
valid; it is caught by the export signature and by the id-order and first_id
checks. Disclosed rather than papered over.

## The check that matters most: truncation against a bundle you already hold

A bundle can prove its own content is intact. It **cannot** prove the ledger was
not wiped before it was made: an attacker with file access deletes every row,
`verify_chain()` truthfully reports an empty valid chain, and an honest export
signs a clean empty bundle. The first version of this module shipped exactly
that hole — total erasure verified green.

The closing control is sequence. Each bundle records the ledger's own head
(`backend_head_id`) and the digest of the previous bundle. `no_truncation`
fails when a later bundle reports a shorter ledger than one already delivered.
This makes **retaining every bundle, in order, a security control** — see D09
§4.5 — and it is why `previous_export_hash` should be set on every export after
the first, and `--previous-bundle` passed to every verification.

`genesis_anchor` closes the same class at the front of the ledger: an unbounded
export must begin at the genesis hash, so rows cannot be deleted from the start
and the remainder exported "honestly".

**Still undetectable, and documented as such:** a clean deletion of the newest
rows, when the recipient holds no earlier bundle. Nothing inside one bundle can
see it.

## Usage

    python3 -m backend.ledger_export keygen --key-file signer.key
    python3 -m backend.ledger_export export --key-file signer.key --out ledger-export.json
    python3 -m backend.ledger_export export --key-file signer.key --after-id 40 --out inc.json
    python3 -m backend.ledger_export verify --key-file signer.key --bundle ledger-export.json
    python3 tools/verify_ledger_export.py --key-file signer.key --bundle ledger-export.json

The last line is the one that matters: it is the check a recipient runs, and it
does not use this file.

## Deliberately not an HTTP route

There is no `/api/ledger/export`. The server has no authentication yet (AD-2,
B01 §7 item 1), and an unauthenticated GET returning every disposition with its
reviewer name and cert ID would be a worse data-handling posture than the gap
it closes. Export is an operator action taken on the box, under the custody
procedure in D09 §4.4. It becomes a web action when AD-2 makes an authenticated
administrator session meaningful — not before.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
from typing import Dict, List, Optional, Tuple

from . import store

FORMAT = "axiom-ledger-export/v1"
HASH_ALGORITHM = "sha256"
SIGNATURE_ALGORITHM = "hmac-sha256"

# Field list the row hash covers, in the order the spec documents them. Both
# verifiers hardcode this tuple rather than reading `manifest["covered_fields"]`
# — a verifier that takes its field list from the bundle it is verifying can be
# told by an attacker which fields to check. The manifest still carries the
# list, so a recipient can *read* what a bundle claims to cover and compare it
# against this file; it is documentation inside the signature, not an input.
COVERED_FIELDS = (
    "advisory_id",
    "reviewer_name",
    "cert_id",
    "disposition",
    "note",
    "recorded_at",
    "supersedes_id",
    "prev_hash",
)

CANONICALISATION = (
    "json.dumps(obj, sort_keys=True, separators=(',', ':')) encoded UTF-8; "
    "row hash = sha256 over the COVERED_FIELDS object; "
    "signature = hmac-sha256 over the canonical form of "
    "{format, manifest, records} (signature excluded)"
)


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
def generate_key() -> bytes:
    """32 random bytes from the OS CSPRNG."""
    return secrets.token_bytes(32)


def load_key(path: str) -> bytes:
    """Read a raw key file. Refuses obvious mistakes rather than silently hashing them."""
    with open(path, "rb") as f:
        key = f.read()
    if len(key) != 32:
        raise ValueError(
            f"signing key must be exactly 32 raw bytes, got {len(key)} in {path}. "
            "If this is a hex or base64 file, decode it first: the key is the raw "
            "bytes, not their textual representation."
        )
    return key


def key_id(key: bytes) -> str:
    """
    A public label for the key: the first 16 hex chars of its SHA-256.

    Safe to publish. It lets a verifier say "this is the wrong key" instead of
    the much less useful "the signature failed", which is the difference
    between a recipient fixing a key mix-up and a recipient concluding they
    have been handed a forged record.
    """
    return hashlib.sha256(key).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Canonical form
# ---------------------------------------------------------------------------
def canonical(obj) -> bytes:
    """The single serialisation used for both row hashes and the signature."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def row_hash(record: Dict[str, object]) -> str:
    """Recompute a row's hash from its documented covered fields."""
    covered = {f: record[f] for f in COVERED_FIELDS}
    return hashlib.sha256(canonical(covered)).hexdigest()


def backend_lead() -> Dict[str, object]:
    """
    What the database itself reports as the end of the ledger.

    This is the anchor that makes erasure detectable. Without it, an attacker
    who deletes every row gets an empty ledger, `verify_chain()` truthfully
    reports "ok, 0 rows", and an honest export signs a clean empty bundle. The
    recipient holding an earlier bundle would see nothing wrong. Recording the
    lead in each bundle means the next one must not report a shorter ledger
    than the one already delivered.
    """
    with store._connect() as conn:
        row = conn.execute(
            "SELECT id, record_hash FROM dispositions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return {
        "backend_head_id": row["id"] if row else None,
        "backend_head_hash": row["record_hash"] if row else store.GENESIS_HASH,
    }


def _unsigned(bundle: Dict[str, object]) -> Dict[str, object]:
    """The bundle content the signature covers: everything but the signature."""
    return {k: bundle[k] for k in ("format", "manifest", "records")}


def sign(bundle: Dict[str, object], key: bytes) -> Dict[str, object]:
    """Return a copy of the bundle with a signature attached."""
    out = dict(bundle)
    out["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": key_id(key),
        "value": hmac.new(key, canonical(_unsigned(out)), hashlib.sha256).hexdigest(),
    }
    return out


def signature_of(bundle: Dict[str, object]) -> str:
    """The bundle's own digest — what a later bundle cites as previous_export_hash."""
    body = {k: bundle[k] for k in ("format", "manifest", "records", "signature")}
    return hashlib.sha256(canonical(body)).hexdigest()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def _fetch(from_id: Optional[int], to_id: Optional[int]) -> List[Dict[str, object]]:
    where, params = [], []
    if from_id is not None:
        where.append("id >= ?")
        params.append(from_id)
    if to_id is not None:
        where.append("id <= ?")
        params.append(to_id)
    sql = (
        "SELECT id, advisory_id, reviewer_name, cert_id, disposition, note, "
        "recorded_at, supersedes_id, prev_hash, record_hash FROM dispositions"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id ASC"
    with store._connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def build_bundle(
    key: bytes,
    from_id: Optional[int] = None,
    to_id: Optional[int] = None,
    after_id: Optional[int] = None,
    previous_export_hash: Optional[str] = None,
) -> Dict[str, object]:
    """
    Build and sign a bundle covering `from_id..to_id` (or `after_id+1..` ).

    `chain_ok` is computed over the **whole** ledger, not the slice, because a
    slice of a broken chain is not a trustworthy slice and saying otherwise
    would be the kind of half-truth this project keeps having to correct.

    A chain break does not prevent the export: refusing to export would let one
    corrupt row destroy the customer's ability to retrieve the rest. It is
    recorded in the manifest, signed, and therefore cannot be quietly dropped
    later.
    """
    if after_id is not None:
        if from_id is not None:
            raise ValueError("pass either from_id or after_id, not both")
        from_id = after_id + 1

    if from_id is not None and to_id is not None and from_id > to_id:
        raise ValueError(
            f"empty range: from_id {from_id} is greater than to_id {to_id}. "
            "This is almost always `--after-id` pointing past the end, so it is "
            "refused rather than signed as a legitimate empty export."
        )

    records = _fetch(from_id, to_id)
    chain = store.verify_chain()
    lead = backend_lead()

    # Reviewer attribution (AD-2). The attestation and the registry entry that
    # makes it nameable ride INSIDE each record rather than in a new top-level
    # bundle field — deliberately. The bundle top level is exactly four signed
    # parts and `bundle_no_extras` refuses anything else, so a top-level
    # attribution block would break every verifier and loosen that check. An
    # extra key inside a record is covered by `signature_of()` and by the
    # bundle signature, and `row_hash()` ignores it because row_hash selects
    # COVERED_FIELDS by name.
    try:
        from . import attribution as _attribution
        attributed = _attribution.attribution_for_export(store.DB_PATH)
        for r in records:
            a = attributed.get(r["id"])
            if a:
                r["attribution"] = a
    except Exception:
        # A missing or unreadable registry must not block an export: losing the
        # ability to retrieve the ledger because the attribution tables are
        # absent would be a worse failure than an unattributed export. The
        # manifest records that attribution was not available, inside the
        # signature, so it cannot be dropped quietly later.
        attributed = {}

    # Chain continuity is checked across the slice as well, as a second,
    # independent reading: the whole-ledger result above is the authority, but a
    # slice that does not link internally must never be signed as if it did.
    slice_ok, slice_reason = _slice_links_ok(records)

    manifest = {
        "exported_at": _now(),
        "database": os.path.basename(store.DB_PATH),
        "schema_version": store.SCHEMA_VERSION,
        "from_id": from_id,
        "to_id": to_id,
        "record_count": len(records),
        "first_id": records[0]["id"] if records else None,
        "last_id": records[-1]["id"] if records else None,
        "first_prev_hash": records[0]["prev_hash"] if records else None,
        # An empty chain's head is the genesis value: there is no last record,
        # and GENESIS_HASH is what "nothing has been appended" hashes to.
        "head_hash": records[-1]["record_hash"] if records else store.GENESIS_HASH,
        "genesis_hash": store.GENESIS_HASH,
        # The ledger's own end, independent of the slice. This is what lets a
        # later bundle prove the ledger did not shrink.
        "backend_head_id": lead["backend_head_id"],
        "backend_head_hash": lead["backend_head_hash"],
        "hash_algorithm": HASH_ALGORITHM,
        "covered_fields": list(COVERED_FIELDS),
        "canonicalisation": CANONICALISATION,
        "ledger_chain_ok": chain["ok"],
        "ledger_rows": chain["rows"],
        "ledger_broken_at_id": chain["broken_at_id"],
        "ledger_break_reason": chain["reason"],
        "slice_links_ok": slice_ok,
        "slice_links_reason": slice_reason,
        "previous_export_hash": previous_export_hash,
        # Attribution availability, stated rather than inferred. A recipient
        # counting attributed records against `attributed_records` must see the
        # numbers agree, or know that the exporter could not read the registry.
        "attribution_available": bool(attributed),
        "attributed_records": sum(1 for r in records if "attribution" in r),
    }

    return sign({"format": FORMAT, "manifest": manifest, "records": records}, key)


def _now() -> str:
    with store._connect() as conn:
        return conn.execute("SELECT datetime('now') AS t").fetchone()["t"]


def _slice_links_ok(records: List[Dict[str, object]]) -> Tuple[bool, Optional[str]]:
    expected = records[0]["prev_hash"] if records else store.GENESIS_HASH
    last_id = None
    for r in records:
        if last_id is not None and r["id"] <= last_id:
            return False, f"ids are not strictly increasing at id {r['id']}"
        if r["prev_hash"] != expected:
            return False, (
                f"prev_hash of id {r['id']} does not match the preceding record "
                "(a record was inserted, removed or reordered)"
            )
        if row_hash(r) != r["record_hash"]:
            return False, f"record_hash of id {r['id']} does not match its content"
        expected = r["record_hash"]
        last_id = r["id"]
    return True, None


# ---------------------------------------------------------------------------
# Verify (the in-repo verifier; the standalone one is the one that counts)
# ---------------------------------------------------------------------------
REQUIRED_ATTRIBUTION_FIELDS = ("attestation", "attested_at", "key_id", "reviewer",
                               "cert_id", "registered_at", "revoked_at")


def _attribution_ordering_bad(rid, a, r):
    """
    The time-order and shape checks an attribution block must satisfy.

    Returned as a (rid, reason) pair rather than appended directly so the two
    verifiers can each call it and produce the same message — the docs live in
    two files but the sentence a recipient reads must be the same one.

    **Absence is a failure, not a skip.** The first version guarded every
    comparison with truthiness (`if a.get("revoked_at") and ...`), so deleting
    the field disabled the check and a re-signed bundle verified clean. A
    recipient with the reviewer key would still have caught the forgery through
    the HMAC, but a keyless recipient would not, and the keyless recipient is
    the common case. Found by audit 2026-11-11.
    """
    missing = [f for f in REQUIRED_ATTRIBUTION_FIELDS if f not in a]
    if missing:
        return (rid, "attribution is missing required field(s) %s"
                % ", ".join(missing))
    for field, value in (("attestation", a["attestation"]),
                         ("attested_at", a["attested_at"]),
                         ("key_id", a["key_id"]),
                         ("registered_at", a["registered_at"])):
        if not isinstance(value, str):
            return (rid, "attribution field %r must be a string, got %s"
                    % (field, type(value).__name__))
    if a["revoked_at"] is not None and not isinstance(a["revoked_at"], str):
        return (rid, "attribution field 'revoked_at' must be a string or null")
    if a["attested_at"] < a["registered_at"]:
        return (rid, "attestation predates the registration of its key")
    if a["revoked_at"] is not None and isinstance(r.get("recorded_at"), str) \
            and r["recorded_at"] > a["revoked_at"]:
        return (rid, "row was recorded after its key was revoked")
    return None


def verify_bundle(
    bundle: Dict[str, object],
    key: bytes,
    previous_bundle: Optional[Dict[str, object]] = None,
    reviewer_keys: Optional[Dict[str, bytes]] = None,
) -> Dict[str, object]:
    """
    Check a bundle. Returns
        {"ok": bool, "checks": [{"name", "ok", "detail"}], "failed": [names]}

    Every check runs; the result is not short-circuited, so a recipient sees the
    whole picture rather than the first thing that broke.
    """
    checks: List[Dict[str, object]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        # Detail describes the *failure*. Carrying it on a pass prints
        # "PASS id_order — ids are not strictly increasing", which reads as a
        # problem where there is none.
        checks.append({"name": name, "ok": bool(ok), "detail": "" if ok else detail})

    for field in ("format", "manifest", "records", "signature"):
        if field not in bundle:
            check("bundle_structure", False, f"missing '{field}'")
            return _result(checks)

    # Nothing but the four covered parts may ride along. This was found on
    # 2026-11-10 by trying it: add any top-level key to a written bundle and the
    # signature still verified, because the signature and the digest both select
    # named fields rather than covering the document. The added key is not signed
    # — so it can be changed after signing without detection — and a recipient
    # reading it would reasonably believe it was covered by the bundle it sits in.
    # Rejecting the bundle is the right answer: a body that is not exactly what
    # was signed cannot be attested to, and no legitimate writer adds a field.
    extra = sorted(set(bundle) - {"format", "manifest", "records", "signature"})
    check("bundle_no_extras", not extra,
          f"bundle carries field(s) outside the signed body and cannot be "
          f"attested: {', '.join(extra)}")
    if extra:
        return _result(checks)

    check("format", bundle["format"] == FORMAT,
          f"expected {FORMAT}, got {bundle['format']}")

    m = bundle["manifest"]
    records = bundle["records"]
    sig = bundle["signature"]

    # --- shape -----------------------------------------------------------
    # A malformed bundle must produce named failures, never a traceback. A
    # recipient who gets a stack trace learns nothing and may conclude the tool
    # is broken rather than that the bundle is bad — the two lead to opposite
    # decisions.
    if not isinstance(m, dict) or not isinstance(records, list) or not isinstance(sig, dict):
        check("bundle_shape", False,
              "manifest must be an object, records an array and signature an object")
        return _result(checks)
    if not all(isinstance(r, dict) for r in records):
        check("bundle_shape", False, "every entry in records must be an object")
        return _result(checks)

    # --- signature -------------------------------------------------------
    check("key_id", sig.get("key_id") == key_id(key),
          "this bundle was signed with a different key"
          if sig.get("key_id") != key_id(key) else "")
    expected_sig = hmac.new(key, canonical(_unsigned(bundle)), hashlib.sha256).hexdigest()
    check("signature", hmac.compare_digest(str(sig.get("value", "")), expected_sig),
          "the bundle content does not match its signature"
          if not hmac.compare_digest(str(sig.get("value", "")), expected_sig) else "")
    check("signature_algorithm", sig.get("algorithm") == SIGNATURE_ALGORITHM,
          f"unsupported algorithm {sig.get('algorithm')!r}")

    # --- coverage --------------------------------------------------------
    # Every record must carry an integer id. Without this, a null id would sit
    # in `ids` and the ordering checks below would compare None with ints — a
    # TypeError, not a verdict.
    if not all(isinstance(r.get("id"), int) and not isinstance(r.get("id"), bool)
               for r in records):
        check("bundle_shape", False, "every record must carry an integer id")
        return _result(checks)

    declared = m.get("record_count")
    try:
        declared_n = int(declared)
    except (TypeError, ValueError):
        declared_n = -1
        check("record_count", False, f"record_count is not a number: {declared!r}")
    if declared_n != -1:
        check("record_count", declared_n == len(records),
              f"manifest says {declared}, bundle contains {len(records)}")
    ids = [r["id"] for r in records]
    check("first_id", (ids[0] if ids else None) == m.get("first_id"),
          f"manifest says {m.get('first_id')}")
    check("last_id", (ids[-1] if ids else None) == m.get("last_id"),
          f"manifest says {m.get('last_id')}")
    check("id_order", all(a < b for a, b in zip(ids, ids[1:])) if len(ids) > 1 else True,
          "ids are not strictly increasing")
    if m.get("from_id") is not None:
        # An empty slice bounded from below is legitimate when the ledger's
        # head is below the bound — nothing has been recorded since the last
        # export. Only a *populated* slice must start at or after from_id.
        head = m.get("backend_head_id")
        empty_and_quiet = (not ids) and (head is None or head < m["from_id"])
        check("range_from", empty_and_quiet or (bool(ids) and ids[0] >= m["from_id"]),
              f"a record precedes the declared from_id {m['from_id']}")
    if m.get("to_id") is not None:
        check("range_to", bool(ids) and ids[-1] <= m["to_id"],
              f"a record follows the declared to_id {m['to_id']}")

    # A bundle that declares no lower bound is a FULL export and must start at
    # the beginning of the chain. Without this, an attacker deletes rows 1..4
    # and exports "honestly" from row 5 with from_id omitted; every other check
    # passes forever because nothing ties an unbounded export to genesis.
    # An unbounded export must start at the beginning of the chain. An empty
    # bundle has no first record to anchor, so the check applies only when
    # there is a record to check — `empty_bundle_justified` covers the empty
    # case, where an unbounded empty export is legitimate only if the ledger
    # itself is empty.
    if m.get("from_id") is None and records:
        check("genesis_anchor",
              m.get("first_prev_hash") == store.GENESIS_HASH,
              "an unbounded export must begin at the genesis hash, but its first "
              "record links to %r — records before it have been removed"
              % (m.get("first_prev_hash"),))

    # --- per-row integrity ----------------------------------------------
    bad = []
    for r in records:
        missing = [f for f in COVERED_FIELDS if f not in r]
        if missing:
            bad.append((r.get("id"), f"missing fields {missing}"))
            continue
        if row_hash(r) != r.get("record_hash"):
            bad.append((r.get("id"), "record_hash does not match content"))
    check("row_hashes", not bad,
          "; ".join(f"id {i}: {why}" for i, why in bad[:5]) +
          (f" (and {len(bad) - 5} more)" if len(bad) > 5 else ""))

    # --- chain continuity within the slice -------------------------------
    expected = m.get("first_prev_hash")
    first_bad = None
    for r in records:
        if r.get("prev_hash") != expected:
            first_bad = r.get("id")
            break
        expected = r.get("record_hash")
    check("prev_hash_links", first_bad is None,
          f"prev_hash of id {first_bad} does not match the preceding record"
          if first_bad is not None else "")
    check("head_hash", (records[-1].get("record_hash") if records else store.GENESIS_HASH)
          == m.get("head_hash"), "head_hash does not match the last record")
    check("genesis_hash", m.get("genesis_hash") in (None, store.GENESIS_HASH),
          "unexpected genesis hash %r" % (m.get("genesis_hash"),))

    # --- attribution (AD-2) -----------------------------------------------
    # What a recipient can establish from the bundle without our database:
    #   * an attested record names the reviewer its own row names, and names
    #     them consistently with the registry entry travelling beside it;
    #   * the attestation does not predate the registration of its key, and the
    #     row it attests was not recorded after that key was revoked — both
    #     comparisons are lexical because SQLite stores `datetime('now')` as
    #     `YYYY-MM-DD HH:MM:SS`, which sorts as text exactly as it sorts in time;
    #   * the attestation value is consistent with the row's record_hash — which
    #     this in-repo verifier CAN check, because it holds the reviewer key;
    #   * the manifest's claim about how many records are attributed matches.
    # A record with no attribution is not a failure. It is an unattributed
    # decision, and the manifest says how many of those there are.
    #
    # **This block is duplicated in tools/verify_ledger_export.py on purpose**
    # and the two must be kept identical in behaviour. The standalone verifier
    # cannot import this module — that is the whole reason it exists — so a
    # change here without the matching change there produces a bundle that
    # passes for us and fails for the recipient, which is the worst possible
    # outcome for a verification story.
    att_bad, att_n = [], 0
    reviewer_keys = reviewer_keys or {}
    # `reviewer_keys` maps key_id -> (key bytes, reviewer the caller believes that
    # key belongs to). The reviewer half matters: without it the `reviewer` field
    # in the block is decorative, because the HMAC covers only `record_hash`. A
    # holder of *any* registered reviewer key could then relabel their own
    # attestation with somebody else's name, and the block's self-declared
    # reviewer would be the only thing asserting otherwise. Found by audit
    # 2026-11-11 — the design claimed "an attestation cannot be moved onto a row
    # naming another reviewer", and at the identity level it could.
    for r in records:
        a = r.get("attribution")
        if not a:
            continue
        att_n += 1
        rid = r.get("id")
        if not isinstance(a, dict):
            att_bad.append((rid, "attribution is not an object"))
            continue
        if a.get("reviewer") != r.get("reviewer_name"):
            att_bad.append((rid, "attribution names %r but the row names %r"
                            % (a.get("reviewer"), r.get("reviewer_name"))))
            continue
        if a.get("cert_id") != r.get("cert_id"):
            att_bad.append((rid, "attribution cert_id does not match the row"))
            continue
        supplied = None
        try:
            supplied = reviewer_keys.get(a.get("key_id"))
        except TypeError:                      # an unhashable key_id, e.g. a list
            att_bad.append((rid, "attribution key_id must be a string"))
            continue
        if supplied is not None:
            key, known_reviewer = supplied
            if known_reviewer is not None and known_reviewer != a.get("reviewer"):
                att_bad.append((rid, "key %s belongs to %r, not %r — the "
                                "attribution names a reviewer the key holder "
                                "was not given as" % (
                                    a.get("key_id"), known_reviewer,
                                    a.get("reviewer"))))
                continue
            want = hmac.new(key, ("axiom-attestation/v1:%s" % r.get("record_hash"))
                            .encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(str(a.get("attestation", "")), want):
                att_bad.append((rid, "attestation does not verify under "
                                     "reviewer key %s" % a.get("key_id")))
        att_bad_ord = _attribution_ordering_bad(rid, a, r)
        if att_bad_ord:
            att_bad.append(att_bad_ord)
    check("attribution_consistent", not att_bad,
          "; ".join("id %s: %s" % (i, w) for i, w in att_bad[:5]))
    # Without the key, "no failure" and "verified" are different outcomes, and
    # reporting them as the same thing is how a verifier starts lying. When the
    # caller supplied keys, every attributed record must have had one.
    if reviewer_keys:
        def _unknown_key(r):
            a = r.get("attribution")
            if not isinstance(a, dict):
                return False
            kid = a.get("key_id")
            if not isinstance(kid, str):
                return False          # already reported by attribution_consistent
            return kid not in reviewer_keys
        unattested_key = [r.get("id") for r in records if _unknown_key(r)]
        check("attestations_verified", not unattested_key,
              "%d attributed record(s) name a key the verifier was not given: %s"
              % (len(unattested_key), unattested_key[:5]))
    declared_att = m.get("attributed_records")
    if declared_att is not None:
        ok_count = isinstance(declared_att, int) and not isinstance(declared_att, bool)
        check("attribution_count", ok_count and declared_att == att_n,
              ("manifest says %r attributed, bundle carries %d"
               % (declared_att, att_n)) if ok_count else
              ("manifest 'attributed_records' must be an integer, got %s"
               % type(declared_att).__name__))
    # `attribution_available: false` with attributed records present is a
    # contradiction; so is `true` with none. Either way the manifest is lying
    # about a property of its own content, which the signature cannot catch
    # because the signer computed the claim.
    if m.get("attribution_available") is not None:
        check("attribution_claim", bool(m["attribution_available"]) == (att_n > 0),
              "manifest claims attribution_available=%r but carries %d "
              "attributed record(s)" % (m["attribution_available"], att_n))

    # --- the ledger's own end, independent of the slice --------------------
    # `backend_head_id`/`backend_head_hash` are what the database reported as
    # its last row. The slice cannot run past that, and the slice's last record
    # must *reach* it — otherwise the export stopped short of the end while
    # claiming to be a complete view to that point.
    bh_id = m.get("backend_head_id")
    bh_hash = m.get("backend_head_hash")
    if records:
        check("backend_head_consistent",
              ids[-1] == bh_id and records[-1].get("record_hash") == bh_hash,
              "the bundle does not end at the record the database reported as its "
              "last (backend_head_id=%r); rows after the export were added or the "
              "manifest was rewritten" % (bh_id,))
    else:
        # An empty bounded slice legitimately stops below the ledger head.
        # An empty *unbounded* slice can only be honest when the ledger is
        # empty; `empty_bundle_justified` checks that separately.
        check("backend_head_consistent",
              m.get("from_id") is not None or bh_id is None,
              "an empty unbounded export reports a ledger head at id %r" % (bh_id,))

    # An empty slice is only legitimate when the ledger itself is empty, or
    # when the slice is bounded by `from_id` (an incremental export that
    # happened to find nothing new). An empty slice from an unbounded export,
    # or from a ledger whose head is non-null, means records vanished.
    if not records:
        empty_ok = (m.get("from_id") is not None) or (m.get("backend_head_id") is None)
        check("empty_bundle_justified", empty_ok,
              "the bundle contains no records but the ledger reported %r rows with "
              "its last at id %r — records have been removed"
              % (m.get("ledger_rows"), m.get("backend_head_id")))

    # --- ledger-wide status, as the exporter reported it -----------------
    check("ledger_chain_ok", m.get("ledger_chain_ok") is True,
          f"the exporting host reported its whole ledger chain broken at id "
          f"{m.get('ledger_broken_at_id')}: {m.get('ledger_break_reason')}"
          if not m.get("ledger_chain_ok") else "")

    # --- continuity with a previously exported bundle --------------------
    if previous_bundle is not None:
        prev_m = previous_bundle.get("manifest", {})
        expected_prev = signature_of(previous_bundle)
        check("previous_export_link",
              m.get("previous_export_hash") == expected_prev,
              "this bundle does not extend the previous one you were given — "
              "records may have been rewritten between the two exports"
              if m.get("previous_export_hash") != expected_prev else "")

        # The check that closes erasure. This bundle must not report a shorter
        # ledger than one you already hold. Without it, deleting every row
        # produces an empty ledger, an honest empty export, and a passing
        # verification — with every earlier record gone and nothing flagged.
        prev_head = prev_m.get("backend_head_id")
        this_head = m.get("backend_head_id")
        if prev_head is not None:
            check("no_truncation",
                  this_head is not None and this_head >= prev_head,
                  "the ledger has SHRUNK since the bundle you hold: this export ends "
                  "at id %r, the previous one ended at id %r. Records have been "
                  "removed." % (this_head, prev_head))

        # The check that closes REWRITING. `no_truncation` compares ids only, so
        # an attacker with file access and no key can rewrite every record,
        # recompute the chain, and export honestly: the ledger still ends at the
        # same id, every internal check passes, and a recipient holding the
        # earlier bundle is told continuity is intact. Found by audit 2026-11-11;
        # reproduced end to end with all 18 checks green while three "flag"
        # dispositions had become "CLEARED".
        #
        # History is immutable by construction: bundle N+1 must EXTEND bundle N,
        # so the record bundle N ended at must still be byte-identical in N+1.
        # Continuity is therefore provable without transmitting the whole
        # ledger — only the anchor the recipient already holds.
        _anchor_history_checks(m, records, prev_m, check)

        # A bounded slice must start beyond the previous bundle's end. An empty
        # incremental has no first_id and is allowed — nothing new was recorded.
        #
        # This check applies to *bounded* (incremental) exports only. A full
        # export is unbounded by definition and re-covers the whole ledger on
        # purpose: it is a re-statement, and that is what makes it the recovery
        # point of a series. Scoping it this way keeps the attack it was written
        # for closed — an incremental overlapping what a recipient already holds
        # — while no longer rejecting the monthly full of a healthy series.
        # `no_truncation` above remains the guard against records disappearing.
        prev_last = prev_m.get("last_id")
        if prev_last is not None and m.get("from_id") is not None:
            check("no_regression",
                  m.get("first_id") is None or m.get("first_id") > prev_last,
                  "this bundle re-covers records already exported (previous ended at "
                  "id %r, this one starts at %r)" % (prev_last, m.get("first_id")))

    return _result(checks)


def _result(checks: List[Dict[str, object]]) -> Dict[str, object]:
    failed = [c["name"] for c in checks if not c["ok"]]
    return {"ok": not failed, "checks": checks, "failed": failed}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cmd_keygen(args) -> int:
    path = args.key_file
    if os.path.exists(path) and not args.force:
        print(f"refusing to overwrite existing key at {path} (pass --force to replace, "
              "which makes every bundle signed with the old key unverifiable against the new one)")
        return 2
    key = generate_key()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        # `os.open`'s mode argument only applies when the file is *created*. On
        # a --force overwrite of a pre-existing 0644 file it is silently
        # ignored, leaving the new key world-readable while the message below
        # claims 0600. Set it explicitly so the claim is true either way.
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(key)
        fd = None
    finally:
        if fd is not None:
            os.close(fd)
    actual = oct(os.stat(path).st_mode & 0o777)
    if actual != "0o600":
        print(f"warning: key file mode is {actual}, expected 0o600 — chmod it before use",
              file=sys.stderr)
    print(f"wrote 32-byte signing key to {path} (mode 0600)")
    print(f"key_id: {key_id(key)}")
    print("Record this key_id in the custody log. Store the key off the platform host.")
    return 0


def _cmd_export(args) -> int:
    key = load_key(args.key_file)
    bundle = build_bundle(
        key,
        from_id=args.from_id,
        to_id=args.to_id,
        after_id=args.after_id,
        previous_export_hash=args.previous_export_hash,
    )
    body = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    sidecar = args.out + ".sha256"
    with open(sidecar, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{digest}  {os.path.basename(args.out)}\n")

    m = bundle["manifest"]
    print(f"wrote {args.out}")
    print(f"  records        {m['record_count']}  (id {m['first_id']}..{m['last_id']})")
    print(f"  head_hash      {m['head_hash']}")
    print(f"  key_id         {bundle['signature']['key_id']}")
    print(f"  bundle digest  {digest}  (also in {os.path.basename(sidecar)})")
    print(f"  ledger chain   {'ok' if m['ledger_chain_ok'] else 'BROKEN — see manifest'}")
    if m["previous_export_hash"] is None:
        print("  previous       none — this bundle does not extend an earlier one")
    return 0


def _anchor_history_checks(m, records, prev_m, check) -> None:
    """Continuity checks that need the previous bundle. Shared by every verifier.

    Kept as one function because the standalone verifier in `tools/` has to
    reproduce this logic without importing it, and a divergence between the two
    is worse than either being wrong: a recipient would see a failure the
    exporter says cannot happen.
    """
    # The anchor is the ledger's OWN head hash, not the slice's `head_hash`.
    # An incremental's `head_hash` names the last record inside that slice —
    # and for a zero-record week it is the genesis value — so chaining off it
    # would compare unrelated things and falsely reject a healthy series.
    # `backend_head_hash` is the hash of the ledger's end regardless of slice,
    # which is the only value that can prove the ledger was not rewritten.
    prev_head_hash = prev_m.get("backend_head_hash")
    prev_head_id = prev_m.get("backend_head_id")
    if prev_head_hash is not None and prev_head_id is not None:
        anchor = next((r.get("record_hash") for r in records
                       if r.get("id") == prev_head_id), None)

        # The anchor is only expected when this bundle's range actually covers
        # it. A weekly incremental starts AFTER the previous bundle's end by
        # design — requiring the anchor there would reject every healthy
        # series, which is exactly what the first cut of this check did. A
        # full export is unbounded and re-covers everything, so it must carry
        # the anchor; so must any bounded slice that starts at or before it.
        from_id = m.get("from_id")
        covers_anchor = (from_id is None or from_id <= prev_head_id) and bool(records)

        if anchor is None and not covers_anchor:
            # Legitimately outside this bundle's range. `previous_export_link`
            # and `no_regression` carry continuity here, and a later full
            # export re-covers the anchor and would expose a rewrite then.
            pass
        elif anchor is None:
            check("history_continues", False,
                  "the previous bundle ended at record id %r, which this export's "
                  "range covers but does not contain — continuity cannot be "
                  "confirmed. Records have been removed." % prev_head_id)
        else:
            check("history_continues", anchor == prev_head_hash,
                  "record id %r was REWRITTEN after the bundle you hold was signed: "
                  "stored hash %r, previous bundle recorded %r. The chain was "
                  "recomputed to match, so every internal check passes — the "
                  "rewrite is visible only against the bundle you already hold." % (
                      prev_head_id, str(anchor)[:16], str(prev_head_hash)[:16]))

    prev_rows = prev_m.get("ledger_rows")
    this_rows = m.get("ledger_rows")
    if prev_rows is not None and this_rows is not None:
        check("no_row_deletion", this_rows >= prev_rows,
              "the ledger now holds %r rows, the bundle you hold reported %r. "
              "Records have been removed from the middle: the head id is "
              "unchanged, so truncation checks cannot see this." % (
                  this_rows, prev_rows))


def _reject_duplicate_keys(pairs):
    """See `tools/verify_ledger_export.py` — the same guard, for the same reason."""
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise ValueError("duplicate key %r in bundle JSON — a bundle must have "
                             "exactly one of each field" % k)
        seen.add(k)
    return dict(pairs)


def _load_bundle(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=_reject_duplicate_keys)


def _cmd_verify(args) -> int:
    key = load_key(args.key_file)
    try:
        bundle = _load_bundle(args.bundle)
        previous = _load_bundle(args.previous_bundle) if args.previous_bundle else None
    except ValueError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    result = verify_bundle(bundle, key, previous)
    for c in result["checks"]:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['name']}"
              + (f"  — {c['detail']}" if c["detail"] else ""))
    print("OK" if result["ok"] else f"FAILED: {', '.join(result['failed'])}")
    return 0 if result["ok"] else 1


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="backend.ledger_export", description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("keygen", help="generate a 32-byte signing key")
    k.add_argument("--key-file", required=True)
    k.add_argument("--force", action="store_true")
    k.set_defaults(fn=_cmd_keygen)

    e = sub.add_parser("export", help="build and sign an export bundle")
    e.add_argument("--key-file", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--from-id", type=int, default=None)
    e.add_argument("--to-id", type=int, default=None)
    e.add_argument("--after-id", type=int, default=None,
                   help="export only records after this id — the incremental case")
    e.add_argument("--previous-export-hash", default=None,
                   help="signature_of() the previous bundle, to chain exports together")
    e.set_defaults(fn=_cmd_export)

    v = sub.add_parser("verify", help="verify a bundle")
    v.add_argument("--key-file", required=True)
    v.add_argument("--bundle", required=True)
    v.add_argument("--previous-bundle", default=None)
    v.set_defaults(fn=_cmd_verify)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
