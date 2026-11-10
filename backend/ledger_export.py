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
def verify_bundle(
    bundle: Dict[str, object],
    key: bytes,
    previous_bundle: Optional[Dict[str, object]] = None,
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

        # An export that carries records must start beyond the previous
        # bundle's end. An empty incremental export has no first_id and is
        # allowed — it means nothing new was recorded.
        prev_last = prev_m.get("last_id")
        if prev_last is not None:
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


def _cmd_verify(args) -> int:
    key = load_key(args.key_file)
    with open(args.bundle, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    previous = None
    if args.previous_bundle:
        with open(args.previous_bundle, "r", encoding="utf-8") as f:
            previous = json.load(f)
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
