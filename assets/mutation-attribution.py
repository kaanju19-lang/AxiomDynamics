#!/usr/bin/env python3
"""
Mutation driver for the attribution build, 2026-11-11.

Each mutation is applied to a pristine copy of the repo, the two relevant test
modules are run, and the driver records whether some test went red. A guard that
has never gone red is not a guard, so a mutation that leaves the suite green is
reported as a FINDING rather than a pass.

The repo is never left modified: every file touched is restored from the
in-memory copy in `finally`.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = "/sessions/wizardly-intelligent-turing/mnt/AxiomDynamics"

TARGETS = ["backend/attribution.py", "backend/ledger_export.py",
           "tools/verify_ledger_export.py"]

MUTATIONS = [
    # (label, file, old, new)
    ("M1 attest accepts an unregistered key", "backend/attribution.py",
     "    if not entries:\n        raise ValueError(",
     "    if False:\n        raise ValueError("),
    ("M2 active_key_for reports a revoked key as active", "backend/attribution.py",
     "            return None if r[\"revoked_at\"] else r",
     "            return r"),
    ("M3 attest skips the reviewer match", "backend/attribution.py",
     "    if entry[\"reviewer\"] != row[\"reviewer_name\"]:",
     "    if False and entry[\"reviewer\"] != row[\"reviewer_name\"]:"),
    ("M4 attest skips the cert match", "backend/attribution.py",
     "    if entry[\"cert_id\"] != row[\"cert_id\"]:",
     "    if False and entry[\"cert_id\"] != row[\"cert_id\"]:"),
    # Trigger mutations disable the guard by making its WHEN clause never fire.
    # Renaming the trigger would not disable anything — the trigger would still
    # be created under a new name and still raise.
    ("M5 registry update trigger disabled", "backend/attribution.py",
     "BEFORE UPDATE ON reviewer_keys\nBEGIN",
     "BEFORE UPDATE ON reviewer_keys WHEN 0\nBEGIN"),
    ("M6 registry delete trigger disabled", "backend/attribution.py",
     "BEFORE DELETE ON reviewer_keys\nBEGIN",
     "BEFORE DELETE ON reviewer_keys WHEN 0\nBEGIN"),
    ("M7 registry replace trigger disabled", "backend/attribution.py",
     "BEFORE INSERT ON reviewer_keys\nWHEN EXISTS (SELECT 1 FROM reviewer_keys WHERE id = NEW.id)\nBEGIN",
     "BEFORE INSERT ON reviewer_keys\nWHEN 0\nBEGIN"),
    ("M8 attestation update trigger disabled", "backend/attribution.py",
     "BEFORE UPDATE ON attestations\nBEGIN",
     "BEFORE UPDATE ON attestations WHEN 0\nBEGIN"),
    ("M9 attestation delete trigger disabled", "backend/attribution.py",
     "BEFORE DELETE ON attestations\nBEGIN",
     "BEFORE DELETE ON attestations WHEN 0\nBEGIN"),
    ("M10 attestation replace trigger disabled", "backend/attribution.py",
     "BEFORE INSERT ON attestations\nWHEN EXISTS (SELECT 1 FROM attestations WHERE row_id = NEW.row_id)\nBEGIN",
     "BEFORE INSERT ON attestations\nWHEN 0\nBEGIN"),
    ("M11 registry chain hash not recomputed", "backend/attribution.py",
     "        if _entry_hash(r) != r[\"entry_hash\"]:",
     "        if False and _entry_hash(r) != r[\"entry_hash\"]:"),
    ("M12 registry prev_hash link not checked", "backend/attribution.py",
     "        if r[\"prev_hash\"] != expected:",
     "        if False and r[\"prev_hash\"] != expected:"),
    ("M13 verify_attestations ignores the reviewer name", "backend/attribution.py",
     "        elif row[\"reviewer_name\"] != entry[\"reviewer\"]:",
     "        elif False and row[\"reviewer_name\"] != entry[\"reviewer\"]:"),
    ("M14 verify_attestations never consults the revocation", "backend/attribution.py",
     "        rv = revoked.get(att[\"key_id\"])",
     "        rv = None"),
    ("M15 export never records a revocation beside the registration", "backend/attribution.py",
     "        elif \"revocation\" not in slot:\n            slot[\"revocation\"] = e            # first revocation is the one that counts",
     "        elif False and \"revocation\" not in slot:\n            slot[\"revocation\"] = e"),
    ("M16 attribution value hashed over the wrong message", "backend/attribution.py",
     "    msg = (\"axiom-attestation/v1:\" + str(row[\"record_hash\"])).encode(\"utf-8\")",
     "    msg = (\"axiom-attestation/v1:\" + str(row[\"advisory_id\"])).encode(\"utf-8\")"),
    # --- the exporter verifier ---
    ("M17 exporter skips the reviewer consistency check", "backend/ledger_export.py",
     "        if a.get(\"reviewer\") != r.get(\"reviewer_name\"):",
     "        if False and a.get(\"reviewer\") != r.get(\"reviewer_name\"):"),
    ("M18 exporter skips the cert consistency check", "backend/ledger_export.py",
     "        if a.get(\"cert_id\") != r.get(\"cert_id\"):",
     "        if False and a.get(\"cert_id\") != r.get(\"cert_id\"):"),
    ("M19 exporter skips the registration-order check", "backend/ledger_export.py",
     "    if a[\"attested_at\"] < a[\"registered_at\"]:\n        return (rid, \"attestation predates the registration of its key\")",
     "    if False and a[\"attested_at\"] < a[\"registered_at\"]:\n        return (rid, \"attestation predates the registration of its key\")"),
    ("M20 exporter skips the revocation-order check", "backend/ledger_export.py",
     "    if a[\"revoked_at\"] is not None and isinstance(r.get(\"recorded_at\"), str) \\\n            and r[\"recorded_at\"] > a[\"revoked_at\"]:",
     "    if False and a[\"revoked_at\"] is not None and isinstance(r.get(\"recorded_at\"), str) \\\n            and r[\"recorded_at\"] > a[\"revoked_at\"]:"),
    ("M21 exporter skips the HMAC recompute", "backend/ledger_export.py",
     "            if not hmac.compare_digest(str(a.get(\"attestation\", \"\")), want):",
     "            if False and not hmac.compare_digest(str(a.get(\"attestation\", \"\")), want):"),
    ("M22 exporter never reports unattested keys", "backend/ledger_export.py",
     "        check(\"attestations_verified\", not unattested_key,",
     "        check(\"attestations_verified\", True,"),
    ("M23 exporter skips attribution_count", "backend/ledger_export.py",
     "        check(\"attribution_count\", ok_count and declared_att == att_n,",
     "        check(\"attribution_count\", True,"),
    ("M24 exporter skips attribution_claim", "backend/ledger_export.py",
     "    if m.get(\"attribution_available\") is not None:\n        check(\"attribution_claim\", bool(m[\"attribution_available\"]) == (att_n > 0),",
     "    if False:\n        check(\"attribution_claim\", bool(m[\"attribution_available\"]) == (att_n > 0),"),
    # --- the standalone verifier ---
    ("M25 standalone skips the reviewer consistency check", "tools/verify_ledger_export.py",
     "        if a.get(\"reviewer\") != r.get(\"reviewer_name\"):",
     "        if False and a.get(\"reviewer\") != r.get(\"reviewer_name\"):"),
    ("M26 standalone skips the cert consistency check", "tools/verify_ledger_export.py",
     "        if a.get(\"cert_id\") != r.get(\"cert_id\"):",
     "        if False and a.get(\"cert_id\") != r.get(\"cert_id\"):"),
    ("M27 standalone skips the registration-order check", "tools/verify_ledger_export.py",
     "        if a[\"attested_at\"] < a[\"registered_at\"]:\n            att_bad.append((rid, \"attestation predates the registration of its key\"))",
     "        if False and a[\"attested_at\"] < a[\"registered_at\"]:\n            att_bad.append((rid, \"attestation predates the registration of its key\"))"),
    ("M28 standalone skips the HMAC recompute", "tools/verify_ledger_export.py",
     "            if not hmac.compare_digest(str(a.get(\"attestation\", \"\")), want):",
     "            if False and not hmac.compare_digest(str(a.get(\"attestation\", \"\")), want):"),
    ("M29 standalone never reports unattested keys", "tools/verify_ledger_export.py",
     "        check(\"attestations_verified\", unverifiable == 0,",
     "        check(\"attestations_verified\", True,"),
    ("M30 standalone accepts a mislabelled reviewer key", "tools/verify_ledger_export.py",
     "        if hashlib.sha256(rk).hexdigest()[:16] != kid:",
     "        if False and hashlib.sha256(rk).hexdigest()[:16] != kid:"),
    ("M31 standalone skips attribution_count", "tools/verify_ledger_export.py",
     "        check(\"attribution_count\", ok_count and declared_att == att_n,",
     "        check(\"attribution_count\", True,"),
    ("M32 attribution not attached to exported records", "backend/ledger_export.py",
     "                r[\"attribution\"] = a",
     "                pass"),
    # --- added after the adversarial audit, 2026-11-11 ---
    ("M33 verifier ignores the reviewer name bound to a supplied key",
     "backend/ledger_export.py",
     "            if known_reviewer is not None and known_reviewer != a.get(\"reviewer\"):",
     "            if False and known_reviewer is not None and known_reviewer != a.get(\"reviewer\"):"),
    ("M34 ordering fields are optional again (truthiness guards)", "backend/ledger_export.py",
     "    missing = [f for f in REQUIRED_ATTRIBUTION_FIELDS if f not in a]\n    if missing:",
     "    missing = []\n    if missing:"),
    ("M35 export returns the oldest registration again", "backend/attribution.py",
     "        if e[\"revoked_at\"] is None:\n            slot[\"registration\"] = e          # newest non-revocation wins",
     "        if e[\"revoked_at\"] is None and \"registration\" not in slot:\n            slot[\"registration\"] = e"),
    ("M36 attest never re-checks under the write lock", "backend/attribution.py",
     "        for row2 in conn.execute(\n                \"SELECT revoked_at FROM reviewer_keys WHERE key_id = ? \"\n                \"AND revoked_at IS NOT NULL LIMIT 1\", (kid,)):",
     "        for row2 in []:"),
    ("M37 register accepts a key revoked in its history", "backend/attribution.py",
     "                \"AND revoked_at IS NOT NULL LIMIT 1\", (kid,)):\n            raise ValueError(\n                \"key %s was revoked at %s and cannot be registered back into \"",
     "                \"AND revoked_at IS NOT NULL AND 0 LIMIT 1\", (kid,)):\n            raise ValueError(\n                \"key %s was revoked at %s and cannot be registered back into \""),
    ("M38 standalone revocation-order branch disabled", "tools/verify_ledger_export.py",
     "        if a[\"revoked_at\"] is not None and isinstance(r.get(\"recorded_at\"), str) \\\n                and r[\"recorded_at\"] > a[\"revoked_at\"]:",
     "        if False and a[\"revoked_at\"] is not None and isinstance(r.get(\"recorded_at\"), str) \\\n                and r[\"recorded_at\"] > a[\"revoked_at\"]:"),
    ("M39 standalone ignores the reviewer name bound to a supplied key",
     "tools/verify_ledger_export.py",
     "            if known is not None and known != a.get(\"reviewer\"):",
     "            if False and known is not None and known != a.get(\"reviewer\"):"),
    ("M40 standalone ordering fields are optional again", "tools/verify_ledger_export.py",
     "        missing = [f for f in REQUIRED_ATTRIBUTION_FIELDS if f not in a]\n        if missing:",
     "        missing = []\n        if missing:"),
]


def run_tests():
    """Run the two modules that must catch these mutations."""
    codes = []
    for mod in ("tests/test_attribution.py", "tests/test_export.py"):
        p = subprocess.run([sys.executable, "-I", "-B", os.path.join(REPO, mod)],
                           capture_output=True, text=True, cwd=REPO)
        codes.append((mod, p.returncode, p.stdout))
    return codes


def failed_names(stdout):
    return re.findall(r"^FAIL  (\S+)", stdout, re.M)


SNAPSHOT = "/tmp/mutation-attribution-snapshot"


def snapshot_dir():
    os.makedirs(SNAPSHOT, exist_ok=True)
    return SNAPSHOT


def snapshot_path(target):
    return os.path.join(SNAPSHOT, target.replace("/", "__"))


def save_snapshot(originals):
    """Keep a pristine copy outside the repo, so a run cut off mid-mutation can
    be recovered without touching git."""
    snapshot_dir()
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


def main():
    # `--file <substring>` restricts the run to mutations against one target and
    # `--range A:B` to a slice of that list. Both exist because a full pass runs
    # longer than one tool call is allowed to: a run cut off mid-mutation would
    # leave the tree modified.
    #
    # `--restore` puts the pristine copies back without running anything. It is
    # the recovery path for a run that was killed, and it must be called rather
    # than assumed — a partially applied mutation that happens to compile will
    # quietly weaken a guard and every later test will still pass.
    only = None
    if "--file" in sys.argv:
        only = sys.argv[sys.argv.index("--file") + 1]
    lo, hi = 0, 10 ** 9
    if "--range" in sys.argv:
        a, b = sys.argv[sys.argv.index("--range") + 1].split(":")
        lo, hi = int(a), int(b)

    if "--restore" in sys.argv:
        print("restored %d file(s)" % restore_snapshot())
        return 0

    originals = {}
    for t in TARGETS:
        # newline="" on both read and write so the file's own line endings are
        # preserved byte for byte. Without it Python translates CRLF to LF on
        # read and writes LF back, which rewrites every line of the file and
        # makes the mutation look like a whole-file change.
        with open(os.path.join(REPO, t), encoding="utf-8", newline="") as f:
            originals[t] = f.read()
    save_snapshot(originals)

    baseline = run_tests()
    for mod, code, out in baseline:
        if code != 0:
            print("BASELINE FAILED in %s" % mod)
            print(out[-3000:])
            return 1
    print("baseline green in both modules\n")

    findings, results = [], []
    selected = [m for m in MUTATIONS if only is None or only in m[1]][lo:hi]
    try:
        for label, target, old, new in selected:
            path = os.path.join(REPO, target)
            src = originals[target]
            count = src.count(old)
            if count != 1:
                results.append((label, "SKIP", "pattern matched %d times" % count))
                print("%-58s SKIP (matched %d)" % (label, count))
                continue
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(src.replace(old, new))
            try:
                outs = run_tests()
                killed, names = False, []
                for mod, code, out in outs:
                    if code != 0:
                        killed = True
                        names.extend(failed_names(out))
                status = "KILLED" if killed else "SURVIVED"
                detail = ", ".join(names[:3])
                results.append((label, status, detail))
                print("%-58s %-8s %s" % (label, status, detail))
                if not killed:
                    findings.append(label)
            finally:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(originals[target])
    finally:
        for t, src in originals.items():
            with open(os.path.join(REPO, t), "w", encoding="utf-8", newline="") as f:
                f.write(src)

    print("\n%d mutations, %d killed, %d survived, %d skipped"
          % (len(selected), sum(1 for r in results if r[1] == "KILLED"),
             len(findings), sum(1 for r in results if r[1] == "SKIP")))
    if findings:
        print("\nSURVIVORS (guards that are not guarding):")
        for f_ in findings:
            print("  - " + f_)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
