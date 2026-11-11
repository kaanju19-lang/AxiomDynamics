#!/usr/bin/env python3
"""
Verify a signed reviewer key directory for a recipient, and print the
key_id -> reviewer bindings it carries. **Imports nothing from `backend/`** —
a recipient runs this against the files they were given, on a machine that has
no copy of the Platform (same rule as tools/verify_ledger_export.py).

Usage:
    python3 tools/verify_key_directory.py DIRECTORY.json --key EXPORTKEY.bin
    python3 tools/verify_key_directory.py DIRECTORY.json --key EXPORTKEY.bin \
        --emit-reviewer-keys

Exit status: 0 verified, 1 refused, 2 usage.

`--emit-reviewer-keys` prints one `KEY_ID=REVIEWER:` fragment per live binding,
ready to paste into `tools/verify_ledger_export.py --reviewer-key`, so the
recipient never has to be told a name on a command line.
"""

import argparse
import hashlib
import hmac
import json
import sys

DIRECTORY_FORMAT = "axiom-key-directory/v1"
ENTRY_FIELDS = ("reviewer", "cert_id", "key_id", "registered_at", "revoked_at")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def key_id(key):
    return hashlib.sha256(key).hexdigest()[:16]


def _unsigned(directory):
    return {k: v for k, v in directory.items() if k != "signature"}


def _reject_duplicate_keys(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError("duplicate JSON key %r refused" % k)
        seen[k] = v
    return seen


def load_strict(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=_reject_duplicate_keys)


def verify(directory, key):
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok),
                       "detail": "" if ok else detail})

    def result():
        return {"ok": all(c["ok"] for c in checks), "checks": checks,
                "bindings": {}}

    if not isinstance(directory, dict):
        check("directory_shape", False, "not a JSON object")
        return result()

    expected = {"format", "generated_at", "entries", "signature"}
    extra = sorted(set(directory) - expected)
    missing = sorted(expected - set(directory))
    check("directory_no_extras", not extra,
          "fields outside the signed body: %s" % ", ".join(extra))
    check("directory_complete", not missing, "missing: %s" % ", ".join(missing))
    if extra or missing:
        return result()

    check("format", directory["format"] == DIRECTORY_FORMAT,
          "expected %s, got %r" % (DIRECTORY_FORMAT, directory["format"]))
    if directory["format"] != DIRECTORY_FORMAT:
        return result()

    sig = directory["signature"]
    if not isinstance(sig, dict):
        check("signature_shape", False, "signature is not an object")
        return result()

    check("signature_algorithm", sig.get("algorithm") == "hmac-sha256",
          "unsupported algorithm %r" % (sig.get("algorithm"),))
    check("key_id", sig.get("key_id") == key_id(key),
          "signed with a different key (directory says %r, yours %r)"
          % (sig.get("key_id"), key_id(key)))
    want = hmac.new(key, canonical(_unsigned(directory)),
                    hashlib.sha256).hexdigest()
    check("signature", hmac.compare_digest(str(sig.get("value", "")), want))

    entries = directory["entries"]
    if not isinstance(entries, list):
        check("entries_shape", False, "entries is not an array")
        return result()

    bindings, revoked, problems = {}, {}, []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            problems.append("entry %d is not an object" % i)
            continue
        miss = [f for f in ENTRY_FIELDS if f not in e]
        if miss:
            problems.append("entry %d lacks %s" % (i, ", ".join(miss)))
            continue
        kid = e["key_id"]
        if not isinstance(kid, str) or len(kid) != 16:
            problems.append("entry %d has a malformed key_id" % i)
            continue
        if kid in bindings and bindings[kid] != e["reviewer"]:
            problems.append("key_id %s bound to two reviewers (%r and %r)"
                            % (kid, bindings[kid], e["reviewer"]))
            continue
        bindings[kid] = e["reviewer"]
        if e.get("revoked_at"):
            revoked[kid] = True

    check("entries_consistent", not problems, "; ".join(problems))
    live = {kid: n for kid, n in bindings.items() if not revoked.get(kid)}
    check("live_bindings_present", bool(live), "no live key binding")
    return {"ok": all(c["ok"] for c in checks), "checks": checks,
            "bindings": live}


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Verify a signed reviewer key directory.")
    p.add_argument("directory")
    p.add_argument("--key", required=True,
                   help="the 32-byte export key the directory was signed with")
    p.add_argument("--json", action="store_true")
    p.add_argument("--emit-reviewer-keys", action="store_true",
                   help="print KEY_ID=REVIEWER: fragments for "
                        "tools/verify_ledger_export.py")
    a = p.parse_args(argv)

    with open(a.key, "rb") as f:
        key = f.read()
    if len(key) != 32:
        print("the export key must be exactly 32 raw bytes, got %d" % len(key),
              file=sys.stderr)
        return 2

    try:
        directory = load_strict(a.directory)
    except ValueError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1

    result = verify(directory, key)

    if a.json:
        print(json.dumps(result, indent=2))
    else:
        for c in result["checks"]:
            print("%-24s %s%s" % (c["name"], "ok" if c["ok"] else "FAIL",
                                  "  - " + c["detail"] if c["detail"] else ""))
        print()
        if result["ok"]:
            print("VERIFIED: %d live reviewer binding(s)" %
                  len(result["bindings"]))
        else:
            print("REFUSED: the directory does not verify")

    if a.emit_reviewer_keys and result["bindings"]:
        print("\n--reviewer-key fragments (append :PATH to each):")
        for kid in sorted(result["bindings"]):
            print("  %s=%s:" % (kid, result["bindings"][kid]))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
