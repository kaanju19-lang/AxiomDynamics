#!/usr/bin/env python3
"""
Issue a reviewer credential: generate the key, register it, print the key_id.

This is the joiner step in D09 §8.4.2. It exists because that procedure named
an action nobody could perform — a reviewer key could only be created by
`tools/seed_demo_account.py`, which generates one and *discards it* (correctly:
printing a demo key would be the worst thing that script could do). A procedure
that cannot be carried out is not a control, so the missing piece is here.

What it does, in order, because the second refuses unless the first succeeded:

  1. generate 32 bytes from the OS CSPRNG and write them mode 0600;
  2. register the key against a reviewer and certificate (`attribution.register`);
  3. print the `key_id` for the custody log (D09 §8.4.6) — **never the key**.

The certificate must already exist in the registry or be created by this call:
`register` binds the key to a `cert_id`, and `accounts.enroll` later refuses an
account whose certificate is not live. Registering the certificate is part of
issuing the credential, so this tool does both by default.

Usage::

    python3 -I tools/issue_reviewer_key.py \\
        --reviewer "Hoffman" --cert CERT-H-1 --key-file /secure/hoffman.key

The certificate is registered by this call. Registering the key is not
optional and has no separate switch: an unregistered key attests nothing.

**The key file is written to a path you choose and is not backed up for you.**
That is deliberate: D09 §8.4.1 forbids storing it beside the bundles it signs or
on the export media. Move it to the reviewer's custody, or the Railroad's
sealed store, and record where in the custody log.

Refuses to overwrite an existing key file. A silent overwrite here destroys the
only copy of a credential, and the registry cannot be repaired afterwards.
"""

from __future__ import annotations

import argparse
import os
import secrets
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _write_secret(path: str, key: bytes) -> None:
    """Create `path` exclusively, mode 0600, and write the key."""
    # O_EXCL so a second run cannot destroy the first key. The registry forbids
    # re-registering revoked bytes, but a lost key is not recoverable even if
    # the registry entry survives.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--reviewer", required=True,
                    help="display name the key attributes; one reviewer per key")
    ap.add_argument("--cert", required=True,
                    help="certificate ID the key is bound to")
    ap.add_argument("--key-file", required=True,
                    help="where to write the 32-byte key (mode 0600, must not exist)")
    ap.add_argument("--note", default="", help="registry note, e.g. the F08 reference")
    ap.add_argument("--db", default=None,
                    help="axiom.db path; defaults to the Platform's own")
    args = ap.parse_args(argv)

    from backend import attribution, store

    db = args.db or store.DB_PATH

    if os.path.exists(args.key_file):
        print("refusing to overwrite %s — a key file is the only copy of a "
              "credential. Move it aside or choose another path."
              % args.key_file, file=sys.stderr)
        return 2

    key = secrets.token_bytes(32)
    try:
        entry = attribution.register(db, args.reviewer, args.cert, key,
                                     note=args.note)
    except ValueError as exc:
        # Nothing was written; do not leave a key file behind for a key the
        # registry refused.
        print("register: %s" % exc, file=sys.stderr)
        print("\nNo key file was written.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        # An unopenable database, a locked file, a permissions problem. The
        # operator needs a refusal, not a traceback — and they need to know no
        # key file was written, which is the thing they would otherwise have to
        # check by looking.
        print("register failed: %s: %s" % (type(exc).__name__, exc),
              file=sys.stderr)
        print("\nNo key file was written.", file=sys.stderr)
        return 1

    try:
        _write_secret(args.key_file, key)
    except OSError as exc:
        # The registry entry now exists and cannot be removed. That is a real
        # problem and must be reported rather than swallowed: revoke the
        # registration for cause (it has no usable key file) and issue again.
        print("WARNING: %s registered %r under %s, but the key file could not "
              "be written (%s)." % (entry["key_id"], args.reviewer,
                                    args.cert, exc), file=sys.stderr)
        print("Revoke this registration (attribution.revoke) and issue a new "
              "key — the registered bytes exist only in this process and are "
              "about to be lost.", file=sys.stderr)
        return 3

    kid = attribution.key_id(key)
    print("issued       %r under %s" % (args.reviewer, args.cert))
    print("key_id       %s" % kid)
    print("key file     %s (mode 0600)" % args.key_file)
    print("\nRecord in the custody log (D09 §8.4.6) — date, 'joined', reviewer,")
    print("certificate, key_id %s, where the file is held, and who issued it." % kid)
    print("Do NOT record the key itself anywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
