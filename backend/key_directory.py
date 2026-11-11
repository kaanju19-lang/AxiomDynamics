"""
The signed reviewer key directory — AD-2's transferability piece.

**The gap this closes.** An attestation made with a reviewer's HMAC is only
meaningful if the recipient knows which key belongs to whom. Until now that
knowledge lived on the verifier's command line: `--reviewer-key
KEYID=NAME:path`. A recipient told nothing could not check the label, and a
recipient told the wrong name would check against the wrong thing and either
pass a forgery or fail an honest bundle with no way to tell which.

**What the directory is.** A signed document that states the binding: for each
reviewer, the key_id and cert_id that were issued to them, when, and whether
that binding has since been revoked. It carries **no key material** — a key_id
is a truncated digest of the key, so publishing it reveals nothing that lets
anyone forge. Signing the binding is what makes it usable by a third party: a
recipient verifies the directory once, then trusts its bindings for every
bundle it checks.

**What it proves, and what it must never be read as proving.** It is signed
with the same symmetric HMAC export key the bundles use. That means it proves
the holder of the export key authored this list of bindings. It does **not**
prove the export key holder is entitled to author them — that remains the
custody procedure and, ultimately, an asymmetric signature with a published
public key (B01 §7 item 11). It says nothing about whether a reviewer was at
the keyboard. And because it is symmetric, a recipient holding the export key
could produce a directory of their own; the security it adds is against a
recipient who does *not* hold that key, which is the normal verification case.

The honest sentence: **the directory makes the key-to-name binding portable and
tamper-evident. It does not make it authenticated, because the signature is
symmetric.** That is a real improvement over a name typed on a command line
and it is not the same as a certificate authority.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional

DIRECTORY_FORMAT = "axiom-key-directory/v1"
SIGNATURE_ALGORITHM = "hmac-sha256"

# The fields a directory entry carries. Whitelisted so a registry row gaining a
# column cannot silently leak into the signed body — the same reason an export
# bundle refuses extra top-level fields.
ENTRY_FIELDS = ("reviewer", "cert_id", "key_id", "registered_at", "revoked_at")


def canonical(obj: Any) -> bytes:
    """Deterministic JSON. Shared convention with the export signer."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _unsigned(directory: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in directory.items() if k != "signature"}


def key_id(key: bytes) -> str:
    """The public label for a key: first 16 hex of its SHA-256. Same as registry."""
    return hashlib.sha256(key).hexdigest()[:16]


def build(db_path: str, generated_at: Optional[str] = None) -> Dict[str, Any]:
    """
    Build the unsigned directory body from the registry.

    Every registry row becomes one entry, oldest first, including revocations —
    a recipient needs to see that a binding *was* revoked, not just that it is
    gone. A reviewer whose only rows are revoked still appears, with
    `revoked_at` set on their entries.
    """
    from . import attribution

    if not attribution.verify_registry(db_path)["ok"]:
        raise ValueError("the reviewer registry does not verify; refusing to "
                         "publish a directory built from a broken chain")

    entries: List[Dict[str, Any]] = []
    for row in attribution.registry(db_path):
        entries.append({k: row.get(k) for k in ENTRY_FIELDS})

    body = {
        "format": DIRECTORY_FORMAT,
        "generated_at": generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                      time.gmtime()),
        "entries": entries,
    }
    return body


def sign(directory: Dict[str, Any], key: bytes) -> Dict[str, Any]:
    """Attach an HMAC signature over the directory body."""
    if len(key) != 32:
        raise ValueError("the directory signing key must be 32 raw bytes")
    signed = dict(_unsigned(directory))
    signed["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": key_id(key),
        "value": hmac.new(key, canonical(_unsigned(directory)),
                          hashlib.sha256).hexdigest(),
    }
    return signed


def _reject_duplicate_keys(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError("duplicate JSON key %r refused" % k)
        seen[k] = v
    return seen


def load_strict(path: str) -> Dict[str, Any]:
    """Load a directory from disk, refusing duplicate keys."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=_reject_duplicate_keys)


def verify(directory: Dict[str, Any], key: bytes) -> Dict[str, Any]:
    """
    Verify a directory: shape, format, signature, and the entries' internal
    consistency. Returns {"ok": bool, "checks": [...], "bindings": {...}}.

    `bindings` maps key_id -> reviewer name for every entry that is not
    revoked, so a caller can feed it straight to the bundle verifier instead of
    collecting `--reviewer-key` arguments by hand.
    """
    checks: List[Dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok),
                       "detail": "" if ok else detail})

    if not isinstance(directory, dict):
        check("directory_shape", False, "not a JSON object")
        return {"ok": False, "checks": checks, "bindings": {}}

    expected_top = {"format", "generated_at", "entries", "signature"}
    extra = sorted(set(directory) - expected_top)
    missing = sorted(expected_top - set(directory))
    check("directory_no_extras", not extra,
          "fields outside the signed body: %s" % ", ".join(extra))
    check("directory_complete", not missing,
          "missing: %s" % ", ".join(missing))
    if extra or missing:
        return {"ok": False, "checks": checks, "bindings": {}}

    check("format", directory["format"] == DIRECTORY_FORMAT,
          "expected %s, got %r" % (DIRECTORY_FORMAT, directory["format"]))
    if directory["format"] != DIRECTORY_FORMAT:
        return {"ok": False, "checks": checks, "bindings": {}}

    sig = directory["signature"]
    if not isinstance(sig, dict):
        check("signature_shape", False, "signature is not an object")
        return {"ok": False, "checks": checks, "bindings": {}}

    check("signature_algorithm", sig.get("algorithm") == SIGNATURE_ALGORITHM,
          "unsupported algorithm %r" % (sig.get("algorithm"),))
    check("key_id", sig.get("key_id") == key_id(key),
          "this directory was signed with a different key")

    want = hmac.new(key, canonical(_unsigned(directory)),
                    hashlib.sha256).hexdigest()
    check("signature", hmac.compare_digest(str(sig.get("value", "")), want))

    entries = directory["entries"]
    if not isinstance(entries, list):
        check("entries_shape", False, "entries is not an array")
        return {"ok": False, "checks": checks, "bindings": {}}

    bindings: Dict[str, str] = {}
    revoked: Dict[str, bool] = {}
    problems: List[str] = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            problems.append("entry %d is not an object" % i)
            continue
        missing_e = [f for f in ENTRY_FIELDS if f not in e]
        if missing_e:
            problems.append("entry %d lacks %s" % (i, ", ".join(missing_e)))
            continue
        kid = e["key_id"]
        if not isinstance(kid, str) or len(kid) != 16:
            problems.append("entry %d has a malformed key_id" % i)
            continue
        # One key_id must name one reviewer for its whole life. Two reviewers
        # sharing a key_id means one key was registered to two names, which is
        # exactly the relabelling the directory exists to catch.
        if kid in bindings and bindings[kid] != e["reviewer"]:
            problems.append("key_id %s is bound to two reviewers (%r and %r)"
                            % (kid, bindings[kid], e["reviewer"]))
            continue
        bindings[kid] = e["reviewer"]
        if e.get("revoked_at"):
            revoked[kid] = True

    check("entries_consistent", not problems, "; ".join(problems))

    # A live binding is one that was never revoked. A key_id revoked at some
    # point is dropped from the usable set even if a later row re-registered it
    # under a fresh key, because the directory is telling you what to trust now.
    live = {kid: name for kid, name in bindings.items() if not revoked.get(kid)}
    check("live_bindings_present", bool(live),
          "no reviewer has a live key binding; the directory cannot verify "
          "any attestation")

    return {"ok": all(c["ok"] for c in checks), "checks": checks,
            "bindings": live}


def save(directory: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(directory, f, indent=2, sort_keys=True)
        f.write("\n")
