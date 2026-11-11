#!/usr/bin/env python3
"""
Mutation driver for chat-7's guards, 2026-11-11.

Two things are under test:

  * the ingest credential gate — the shape chat-6's inert guard taught us to
    hunt for: a check that runs but whose result the caller discards, or a
    check that happens after the write it was meant to prevent;
  * the key directory's consistency check — the one that refuses one key_id
    naming two reviewers, which is the only guard that survives an attacker
    who can sign their own directory.

Each mutation is applied to a pristine copy, the relevant test modules are run,
and the driver records whether some test went red. A mutation that leaves the
suite green is reported as a FINDING: a guard that has never gone red is not a
guard. Every file touched is restored in `finally`, and a snapshot is kept in
/tmp so a run cut off mid-mutation can be recovered with --restore.

Usage:
    python3 assets/mutation-ingest-auth.py
    python3 assets/mutation-ingest-auth.py --restore
"""
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = ["backend/main.py", "backend/ingest_auth.py",
           "backend/key_directory.py"]

TESTS = ["tests/test_ingest.py", "tests/test_ingest_auth.py",
         "tests/test_key_directory.py"]

MUTATIONS = [
    # --- the ingest gate in do_POST -------------------------------------
    ("M1 auth-mode check removed: closed deployment accepts traffic",
     "backend/main.py",
     '                if mode == ingest_auth.AUTH_NONE:',
     '                if False and mode == ingest_auth.AUTH_NONE:'),
    ("M2 missing-token check removed", "backend/main.py",
     '                if not token:\n                    return self._send_json(\n                        {"error": "authentication required: send \'Authorization: "\n                                  "Bearer <token>\' from the collector enrollment",\n                         "auth_mode": mode}, status=401)',
     '                if False:\n                    return self._send_json(\n                        {"error": "authentication required",\n                         "auth_mode": mode}, status=401)'),
    ("M3 resolve failure ignored: an unknown token proceeds", "backend/main.py",
     '                try:\n                    collector = ingest_auth.resolve_token(store.DB_PATH, token)\n                except ValueError as exc:\n                    return self._send_json(\n                        {"error": str(exc), "auth_mode": mode}, status=401)',
     '                try:\n                    collector = ingest_auth.resolve_token(store.DB_PATH, token)\n                except ValueError:\n                    collector = {"collector_id": 0, "collector_name": "?"}'),
    # The defect chat-6 found, reproduced here: the gate moves back below the
    # body read, so garbage is logged before the credential is checked.
    ("M4 auth moved after the malformed-body log (the chat-6 shape)",
     "backend/main.py",
     '                try:\n                    body = json.loads(raw.decode("utf-8")) if raw else None\n                except (UnicodeDecodeError, json.JSONDecodeError) as exc:',
     '                if False:\n                    body = json.loads(raw.decode("utf-8")) if raw else None\n                else:\n                    body = None\n                if False:\n                    pass\n                elif False:\n                    pass\n                elif not isinstance(body, (dict, type(None))):\n                    pass\n                if False:\n                    pass'),
    # --- the route's own re-check ---------------------------------------
    ("M5 route skips its token re-resolution", "backend/main.py",
     '    try:\n        collector = ingest_auth.resolve_token(store.DB_PATH, token)\n    except ValueError as exc:\n        return {"error": str(exc), "auth_mode": mode}, 401\n\n    result = ingest.ingest_and_record(store.DB_PATH, body)',
     '    collector = {"collector_id": 0, "collector_name": "?"}\n    result = ingest.ingest_and_record(store.DB_PATH, body)'),
    # --- ingest_auth.py -------------------------------------------------
    ("M6 resolve_token accepts any digest", "backend/ingest_auth.py",
     '            "WHERE token_hash = ? AND revoked_at IS NULL",\n            (digest,)).fetchone()',
     '            "WHERE ? IS NOT NULL AND revoked_at IS NULL",\n            (digest,)).fetchone()'),
    ("M7 auth_mode reports required with nothing enrolled", "backend/ingest_auth.py",
     '    return AUTH_REQUIRED if n else AUTH_NONE',
     '    return AUTH_REQUIRED'),
    ("M8 enrollment guard removed: a revoked name can be re-enrolled",
     "backend/ingest_auth.py",
     '        if dup is not None:\n            raise ValueError("collector %r is already enrolled" % name)',
     '        if False:\n            raise ValueError("collector %r is already enrolled" % name)'),
    ("M9 chain hash check removed", "backend/ingest_auth.py",
     '        if row["entry_hash"] != expected_hash:',
     '        if False and row["entry_hash"] != expected_hash:'),
    ("M10 chain prev_hash check removed", "backend/ingest_auth.py",
     '        if row["prev_hash"] != prev_hash:',
     '        if False and row["prev_hash"] != prev_hash:'),
    ("M11 update trigger disabled", "backend/ingest_auth.py",
     'BEFORE UPDATE ON ingest_collectors\n    BEGIN',
     'BEFORE UPDATE ON ingest_collectors WHEN 0\n    BEGIN'),
    ("M12 delete trigger disabled", "backend/ingest_auth.py",
     'BEFORE DELETE ON ingest_collectors\n    BEGIN',
     'BEFORE DELETE ON ingest_collectors WHEN 0\n    BEGIN'),
    # --- key_directory.py ------------------------------------------------
    ("M13 directory drops the one-key-one-reviewer check", "backend/key_directory.py",
     '        if kid in bindings and bindings[kid] != e["reviewer"]:',
     '        if False and kid in bindings and bindings[kid] != e["reviewer"]:'),
    ("M14 directory accepts extra top-level fields", "backend/key_directory.py",
     '    check("directory_no_extras", not extra,',
     '    check("directory_no_extras", True,'),
    ("M15 directory skips the signature comparison", "backend/key_directory.py",
     '    check("signature", hmac.compare_digest(str(sig.get("value", "")), want))',
     '    check("signature", True)'),
    ("M16 directory reports a revoked binding as live", "backend/key_directory.py",
     '    live = {kid: name for kid, name in bindings.items() if not revoked.get(kid)}',
     '    live = dict(bindings)'),
    ("M17 directory accepts a directory with no live binding", "backend/key_directory.py",
     '    check("live_bindings_present", bool(live),',
     '    check("live_bindings_present", True,'),
    ("M18 directory builds from a registry that does not verify", "backend/key_directory.py",
     '    if not attribution.verify_registry(db_path)["ok"]:',
     '    if False and not attribution.verify_registry(db_path)["ok"]:'),
]

SNAPSHOT = "/tmp/mutation-ingest-snapshot"


def snapshot_path(target):
    return os.path.join(SNAPSHOT, target.replace("/", "__"))


def save_snapshot(originals):
    os.makedirs(SNAPSHOT, exist_ok=True)
    for t, src in originals.items():
        with open(snapshot_path(t), "w", encoding="utf-8", newline="") as f:
            f.write(src)


def restore_snapshot():
    n = 0
    for t in TARGETS:
        p = snapshot_path(t)
        if os.path.exists(p):
            shutil.copyfile(p, os.path.join(REPO, t))
            n += 1
    return n


def run_tests():
    codes = []
    for mod in TESTS:
        p = subprocess.run([sys.executable, "-I", os.path.join(REPO, mod)],
                           capture_output=True, text=True, cwd=REPO)
        codes.append((mod, p.returncode, p.stdout + p.stderr))
    return codes


def failed_names(stdout):
    return re.findall(r"^FAIL  (\S+)", stdout, re.M)


def main():
    if "--restore" in sys.argv:
        print("restored %d file(s)" % restore_snapshot())
        return 0

    originals = {}
    for t in TARGETS:
        with open(os.path.join(REPO, t), encoding="utf-8", newline="") as f:
            originals[t] = f.read()
    save_snapshot(originals)

    baseline = run_tests()
    for mod, code, out in baseline:
        if code != 0:
            print("BASELINE FAILED in %s" % mod)
            print(out[-3000:])
            return 1
    print("baseline green\n")

    killed = survived = 0
    try:
        for i, (label, target, old, new) in enumerate(MUTATIONS, 1):
            src = originals[target]
            if old not in src:
                print("SKIP  %-2d %s  (anchor not found in %s)"
                      % (i, label, target))
                survived += 1
                continue
            if src.count(old) != 1:
                print("SKIP  %-2d %s  (anchor appears %d times)"
                      % (i, label, src.count(old)))
                survived += 1
                continue
            with open(os.path.join(REPO, target), "w",
                      encoding="utf-8", newline="") as f:
                f.write(src.replace(old, new, 1))
            try:
                results = run_tests()
            finally:
                with open(os.path.join(REPO, target), "w",
                          encoding="utf-8", newline="") as f:
                    f.write(src)
            red = []
            for mod, code, out in results:
                if code != 0:
                    red.extend(failed_names(out) or ["<%s nonzero>" % mod])
            if red:
                killed += 1
                print("KILL  %-2d %s" % (i, label))
                print("        %s" % ", ".join(sorted(set(red))[:4]))
            else:
                survived += 1
                print("ALIVE %-2d %s   <-- FINDING: no test went red"
                      % (i, label))
    finally:
        for t, src in originals.items():
            with open(os.path.join(REPO, t), "w", encoding="utf-8",
                      newline="") as f:
                f.write(src)

    print("\n%d mutations: %d killed, %d survived" % (len(MUTATIONS), killed,
                                                      survived))
    return 0 if survived == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
