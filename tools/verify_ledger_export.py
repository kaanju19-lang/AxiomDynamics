#!/usr/bin/env python3
"""
Standalone verifier for an AxiomDynamics ledger export bundle.

**This file imports nothing from `backend/`.** That is the point of it: a
recipient — a regulator, an auditor, the Railroad's own IT team, a successor
vendor — must be able to check a bundle without running, trusting, or even
having the exporting software. If verification required the exporter's code,
"the exporter says it is fine" would be the whole proof.

It needs Python 3.8+ and the standard library. Nothing else. No numpy, no
sqlite3, no network access, no database.

    python3 verify_ledger_export.py --bundle ledger-export.json --key-file signer.key
    python3 verify_ledger_export.py --bundle b2.json --key-file k --previous-bundle b1.json

Exit code 0 means every check passed; 1 means at least one failed and the
failures are named. `--json` prints the full result for a machine to consume.

## What a pass proves

- The bundle is byte-for-byte what was signed, under the stated key (HMAC-SHA256).
- No record inside it has been altered: each `record_hash` recomputes from the
  documented field list.
- No record inside its declared id range is missing, and the `prev_hash` chain
  links end to end inside the slice.
- With `--previous-bundle`: this bundle extends the earlier one, and no record
  previously exported has been dropped or rewritten between them.

## What a pass does NOT prove

- **Who** signed it. HMAC is symmetric: any verifier can also produce this
  signature. Custody and key distribution are the defence; see AD-2, unbuilt.
- **When** it was signed. No external timestamping exists on an air-gapped box.
- **That the ledger was never rewritten before export.** The exporting host
  reports its own chain status in the manifest; a tampered host can report
  "ok". Only the sequence of bundles you hold yourself constrains that.

State these limits when you hand the bundle over. A verification story that
overclaims is worse than none, because the first person who tests it finds out.
"""

import argparse
import hashlib
import hmac
import json
import sys

FORMAT = "axiom-ledger-export/v1"
GENESIS_HASH = "0" * 64
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


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def row_hash(record):
    return hashlib.sha256(canonical({f: record[f] for f in COVERED_FIELDS})).hexdigest()


def key_id(key):
    return hashlib.sha256(key).hexdigest()[:16]


def signature_of(bundle):
    body = {k: bundle[k] for k in ("format", "manifest", "records", "signature")}
    return hashlib.sha256(canonical(body)).hexdigest()


def verify(bundle, key, previous=None):
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail if not ok else ""})

    for field in ("format", "manifest", "records", "signature"):
        if field not in bundle:
            check("bundle_structure", False, "missing '%s'" % field)
            return _result(checks)

    # A bundle must be exactly the four signed parts, nothing else. Added
    # 2026-11-10: any extra top-level key previously rode along unchecked,
    # because both the signature and the digest select named fields rather than
    # covering the document. The extra key is not signed, so it can be changed
    # after signing, and a recipient reading it would think it was covered.
    extra = sorted(set(bundle) - {"format", "manifest", "records", "signature"})
    check("bundle_no_extras", not extra,
          "bundle carries field(s) outside the signed body: %s" % ", ".join(extra))
    if extra:
        return _result(checks)

    check("format", bundle["format"] == FORMAT,
          "expected %s, got %r" % (FORMAT, bundle["format"]))
    if bundle["format"] != FORMAT:
        # The field list is part of the format, not a separate promise. If the
        # format is not the one this verifier implements, stop rather than
        # verify a shape it does not understand.
        return _result(checks)

    m, records, sig = bundle["manifest"], bundle["records"], bundle["signature"]

    # A malformed bundle must produce named failures, never a traceback.
    if not isinstance(m, dict) or not isinstance(records, list) or not isinstance(sig, dict):
        check("bundle_shape", False,
              "manifest must be an object, records an array and signature an object")
        return _result(checks)
    if not all(isinstance(r, dict) for r in records):
        check("bundle_shape", False, "every entry in records must be an object")
        return _result(checks)

    check("signature_algorithm", sig.get("algorithm") == "hmac-sha256",
          "unsupported algorithm %r" % (sig.get("algorithm"),))
    check("key_id", sig.get("key_id") == key_id(key),
          "this bundle was signed with a different key (bundle says %r, your key is %r)"
          % (sig.get("key_id"), key_id(key)))
    expected = hmac.new(key, canonical(
        {k: bundle[k] for k in ("format", "manifest", "records")}), hashlib.sha256).hexdigest()
    check("signature", hmac.compare_digest(str(sig.get("value", "")), expected),
          "the bundle content does not match its signature")

    if not all(isinstance(r.get("id"), int) and not isinstance(r.get("id"), bool)
               for r in records):
        check("bundle_shape", False, "every record must carry an integer id")
        return _result(checks)

    declared = m.get("record_count")
    try:
        declared_n = int(declared)
    except (TypeError, ValueError):
        declared_n = -1
        check("record_count", False, "record_count is not a number: %r" % (declared,))
    if declared_n != -1:
        check("record_count", declared_n == len(records),
              "manifest says %r, bundle contains %d" % (declared, len(records)))
    ids = [r["id"] for r in records]
    check("first_id", (ids[0] if ids else None) == m.get("first_id"),
          "manifest says %r" % (m.get("first_id"),))
    check("last_id", (ids[-1] if ids else None) == m.get("last_id"),
          "manifest says %r" % (m.get("last_id"),))
    check("id_order", all(a < b for a, b in zip(ids, ids[1:])) if len(ids) > 1 else True,
          "ids are not strictly increasing")
    if m.get("from_id") is not None:
        head = m.get("backend_head_id")
        empty_and_quiet = (not ids) and (head is None or head < m["from_id"])
        check("range_from", empty_and_quiet or (bool(ids) and ids[0] >= m["from_id"]),
              "a record precedes the declared from_id %r" % (m["from_id"],))
    if m.get("to_id") is not None:
        check("range_to", bool(ids) and ids[-1] <= m["to_id"],
              "a record follows the declared to_id %r" % (m["to_id"],))

    # An unbounded export must start at the beginning of the chain. An empty
    # bundle has no first record to anchor; `empty_bundle_justified` covers it.
    if m.get("from_id") is None and records:
        check("genesis_anchor", m.get("first_prev_hash") == GENESIS_HASH,
              "an unbounded export must begin at the genesis hash, but its first "
              "record links to %r — records before it have been removed"
              % (m.get("first_prev_hash"),))

    bad = []
    for r in records:
        missing = [f for f in COVERED_FIELDS if f not in r]
        if missing:
            bad.append((r.get("id"), "missing fields %s" % missing))
        elif row_hash(r) != r.get("record_hash"):
            bad.append((r.get("id"), "record_hash does not match content"))
    check("row_hashes", not bad,
          "; ".join("id %s: %s" % (i, why) for i, why in bad[:5])
          + (" (and %d more)" % (len(bad) - 5) if len(bad) > 5 else ""))

    expected_prev = m.get("first_prev_hash")
    first_bad = None
    for r in records:
        if r.get("prev_hash") != expected_prev:
            first_bad = r.get("id")
            break
        expected_prev = r.get("record_hash")
    check("prev_hash_links", first_bad is None,
          "prev_hash of id %s does not match the preceding record" % (first_bad,))
    check("head_hash", (records[-1].get("record_hash") if records else GENESIS_HASH)
          == m.get("head_hash"), "head_hash does not match the last record")
    check("genesis_hash", m.get("genesis_hash") in (None, GENESIS_HASH),
          "unexpected genesis hash %r" % (m.get("genesis_hash"),))

    # The ledger's own end, independent of the slice: the bundle must stop
    # exactly at the row the database reported as its last.
    bh_id = m.get("backend_head_id")
    bh_hash = m.get("backend_head_hash")
    if records:
        check("backend_head_consistent",
              ids[-1] == bh_id and records[-1].get("record_hash") == bh_hash,
              "the bundle does not end at the record the database reported as its "
              "last (backend_head_id=%r); rows after the export were added or the "
              "manifest was rewritten" % (bh_id,))
    else:
        check("backend_head_consistent",
              m.get("from_id") is not None or bh_id is None,
              "an empty unbounded export reports a ledger head at id %r" % (bh_id,))

    # An empty slice is only legitimate when the ledger is empty or the slice
    # is bounded from below by from_id.
    if not records:
        check("empty_bundle_justified",
              (m.get("from_id") is not None) or (m.get("backend_head_id") is None),
              "the bundle contains no records but the ledger reported %r rows with "
              "its last at id %r — records have been removed"
              % (m.get("ledger_rows"), m.get("backend_head_id")))

    # The exporter's own statement about its whole ledger. Not independent
    # evidence — see the module docstring — but a signed admission of a break
    # must never pass as a clean export.
    check("ledger_chain_ok", m.get("ledger_chain_ok") is True,
          "the exporting host reported its ledger chain broken at id %r: %s"
          % (m.get("ledger_broken_at_id"), m.get("ledger_break_reason")))

    if previous is not None:
        pm = previous.get("manifest", {})
        check("previous_export_link", m.get("previous_export_hash") == signature_of(previous),
              "this bundle does not extend the previous one — records may have been "
              "rewritten or removed between the two exports")

        # The check that closes erasure: this bundle must not report a shorter
        # ledger than one already held.
        prev_head = pm.get("backend_head_id")
        this_head = m.get("backend_head_id")
        if prev_head is not None:
            check("no_truncation",
                  this_head is not None and this_head >= prev_head,
                  "the ledger has SHRUNK since the bundle you hold: this export ends "
                  "at id %r, the previous one ended at id %r. Records have been "
                  "removed." % (this_head, prev_head))

        # A *bounded* slice must start beyond the previous bundle's end, or it
        # re-covers records this recipient already holds. A full export is
        # unbounded (`from_id` null) and re-covers the whole ledger on purpose —
        # it is the monthly re-statement of a series, so applying this check to
        # it would reject every legitimate full export of a healthy series.
        # This must match `backend/ledger_export.py` exactly: the two verifiers
        # disagreeing is worse than either being wrong, because a recipient
        # running this one would see a failure the exporter says should not occur.
        prev_last = pm.get("last_id")
        if prev_last is not None and m.get("from_id") is not None:
            check("no_regression",
                  m.get("first_id") is None or m.get("first_id") > prev_last,
                  "this bundle re-covers records already exported (previous ended at "
                  "id %r, this one starts at %r)" % (prev_last, m.get("first_id")))

    return _result(checks)


def _result(checks):
    failed = [c["name"] for c in checks if not c["ok"]]
    return {"ok": not failed, "checks": checks, "failed": failed}


def main(argv=None):
    p = argparse.ArgumentParser(description="Verify an AxiomDynamics ledger export bundle.")
    p.add_argument("--bundle", required=True)
    p.add_argument("--key-file", required=True)
    p.add_argument("--previous-bundle", default=None,
                   help="the previous bundle you hold, to prove this one extends it")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    with open(a.key_file, "rb") as f:
        key = f.read()
    if len(key) != 32:
        print("signing key must be exactly 32 raw bytes, got %d" % len(key), file=sys.stderr)
        return 2
    with open(a.bundle, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    previous = None
    if a.previous_bundle:
        with open(a.previous_bundle, "r", encoding="utf-8") as f:
            previous = json.load(f)

    result = verify(bundle, key, previous)
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        for c in result["checks"]:
            print("%s  %s%s" % ("PASS" if c["ok"] else "FAIL", c["name"],
                                ("  — " + c["detail"]) if c["detail"] else ""))
        if result["ok"]:
            print("\nOK — every check passed. Read the module docstring for what this "
                  "does and does not prove before relying on it.")
        else:
            print("\nFAILED: " + ", ".join(result["failed"]))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
