#!/usr/bin/env python3
"""Benchmark a detached GPG signature, so the cost figure in
`assets/asymmetric-signature-decision-2026-11-13.md` stops being invented.

The paper estimates "tens to low hundreds of milliseconds" for one asymmetric
operation and labels it as invented. This measures it. It isolates the three
components a per-signature cost really has:

  * process start      -- `gpg --version`
  * sign, unprotected  -- the key needs no passphrase
  * sign, protected    -- the key needs a passphrase (this is the realistic case)

A passphrase-protected key normally needs `pinentry`, which is interactive. On a
server that is handled with `--pinentry-mode loopback --passphrase`. That path is
measured separately because it is much slower and it is the one an unattended
edge box would actually use.

Run:  python3 tools/bench_gpg_signature.py [--iters N] [--key-type rsa|ed25519]
It creates a throwaway GNUPGHOME and removes it. It touches no real keyring, and
it performs no network operation.
"""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

PAYLOAD_SIZES = {
    "release-archive": 4 * 1024 * 1024,
    "export-bundle-1000-rows": 512 * 1024,
    "single-attestation": 256,
}


def _run(cmd, env, stdin=None):
    return subprocess.run(
        cmd, env=env, input=stdin, capture_output=True, timeout=120
    )


def _gpg(env, *args, stdin=None):
    return _run(["gpg", "--batch", "--quiet"] + list(args), env, stdin)


def _timed(fn, iters):
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        r = fn()
        dt = (time.perf_counter() - t0) * 1000.0
        if r.returncode != 0:
            raise RuntimeError(
                f"gpg failed rc={r.returncode}: {r.stderr.decode()[:400]}"
            )
        samples.append(dt)
    samples.sort()
    return {
        "n": len(samples),
        "median_ms": round(statistics.median(samples), 2),
        "mean_ms": round(statistics.fmean(samples), 2),
        "p95_ms": round(samples[min(len(samples) - 1, int(len(samples) * 0.95))], 2),
        "min_ms": round(samples[0], 2),
        "max_ms": round(samples[-1], 2),
    }


def make_key(env, key_type, passphrase=None):
    """Generate a throwaway key. Returns the fingerprint."""
    if key_type == "rsa":
        algo = ("--quick-generate-key", f"bench-{time.time_ns()}@invalid",
                "rsa3072", "sign", "never")
    else:
        algo = ("--quick-generate-key", f"bench-{time.time_ns()}@invalid",
                "ed25519", "sign", "never")
    # Options must precede the positional USER-ID/ALGO/USAGE/EXPIRE args, so the
    # pinentry options are spliced in front rather than appended. Loopback is used
    # even for the unprotected key: gpg-agent otherwise tries to open a tty and
    # dies with "Inappropriate ioctl for device" on a headless box, which is
    # exactly the environment this benchmark is meant to describe.
    opts = ["--pinentry-mode", "loopback", "--passphrase", passphrase or ""]
    r = _gpg(env, *opts, *algo)
    if r.returncode != 0:
        raise RuntimeError(f"keygen failed: {r.stderr.decode()[:400]}")
    r = _gpg(env, "--list-keys", "--with-colons")
    for line in r.stdout.decode().splitlines():
        if line.startswith("fpr:"):
            return line.split(":")[9]
    raise RuntimeError("no fingerprint found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=15)
    ap.add_argument("--key-type", choices=["rsa", "ed25519"], default="ed25519")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    if shutil.which("gpg") is None:
        print("gpg not found on PATH; nothing measured.", file=sys.stderr)
        return 2

    home = tempfile.mkdtemp(prefix="bench-gpg-")
    try:
        os.chmod(home, 0o700)
        env = dict(os.environ)
        env["GNUPGHOME"] = home

        result = {
            "gpg_version": _run(["gpg", "--version"], env).stdout.decode().splitlines()[0],
            "key_type": args.key_type,
            "iters": args.iters,
            "measurements": {},
        }

        # 1. process start only
        result["measurements"]["process_start_only"] = _timed(
            lambda: _run(["gpg", "--version"], env), args.iters
        )

        # 2. unprotected signing, by payload size
        fp = make_key(env, args.key_type)
        workdir = tempfile.mkdtemp(prefix="bench-data-")
        try:
            for label, size in PAYLOAD_SIZES.items():
                path = os.path.join(workdir, label + ".bin")
                with open(path, "wb") as fh:
                    fh.write(os.urandom(size))
                sig = path + ".sig"
                if os.path.exists(sig):
                    os.remove(sig)
                result["measurements"][f"sign_unprotected_{label}"] = _timed(
                    lambda p=path, s=sig: _gpg(
                        env, "--yes", "--local-user", fp,
                        "--detach-sign", "--output", s, p
                    ),
                    args.iters,
                )
                # verify is what a recipient pays, and it needs the public key
                result["measurements"][f"verify_{label}"] = _timed(
                    lambda p=path, s=sig: _gpg(env, "--verify", s, p), args.iters
                )
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        # 3. passphrase-protected signing via loopback (the unattended case)
        home2 = tempfile.mkdtemp(prefix="bench-gpg-prot-")
        try:
            os.chmod(home2, 0o700)
            env2 = dict(os.environ)
            env2["GNUPGHOME"] = home2
            fp2 = make_key(env2, args.key_type, passphrase="bench-passphrase")
            workdir = tempfile.mkdtemp(prefix="bench-data2-")
            try:
                path = os.path.join(workdir, "att.bin")
                with open(path, "wb") as fh:
                    fh.write(os.urandom(PAYLOAD_SIZES["single-attestation"]))
                sig = path + ".sig"
                result["measurements"]["sign_passphrase_loopback"] = _timed(
                    lambda: _gpg(
                        env2, "--yes", "--local-user", fp2,
                        "--pinentry-mode", "loopback",
                        "--passphrase", "bench-passphrase",
                        "--detach-sign", "--output", sig, path
                    ),
                    args.iters,
                )
            finally:
                shutil.rmtree(workdir, ignore_errors=True)
        finally:
            shutil.rmtree(home2, ignore_errors=True)

        # Derived: what the export cadence costs per year at the measured median.
        measured = result["measurements"]["sign_unprotected_export-bundle-1000-rows"]
        per_year_ms = measured["median_ms"] * 64
        result["derived"] = {
            "bundle_sign_ms_median": measured["median_ms"],
            "bundles_per_year": 64,
            "total_seconds_per_year": round(per_year_ms / 1000.0, 3),
            "note": "64 = 12 monthly full + 52 weekly incremental, from ledger_replication.due_exports",
        }

        print(json.dumps(result, indent=2))
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(result, fh, indent=2)
                fh.write("\n")
        return 0
    finally:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
