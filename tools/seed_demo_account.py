"""
Create one demo reviewer account on a fresh deployment.

`backend/accounts.auth_mode` fails closed: with no account enrolled, the
disposition write path is closed rather than open. That is correct, and it means
a fresh demo cannot record a decision until somebody deliberately enrolls a
reviewer. This script is that deliberate act.

It does two things that must happen in this order, because the second refuses to
run unless the first succeeded:

  1. register a certification in the reviewer registry (`attribution.register`);
  2. enroll an account bound to that certification (`accounts.enroll`).

Usage::

    python3 -I tools/seed_demo_account.py --username demo --cert DEMO-CERT-001

The passphrase is read from `AXIOM_DEMO_PASSPHRASE` or prompted for, never from
the command line: an argument is visible in the process table to every other user
on the box, and this product exists to be inspected by the Railroad's security
team.

**This is a demo convenience, not a provisioning system.** A real deployment issues
each reviewer their own 32-byte key (which this script does not need and does not
print), their own certificate, and their own account, and also runs the roster
sweeper. Those are AD-2 items on B01 §7 item 1 and are named there as open.
"""

from __future__ import annotations

import argparse
import getpass
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--username", required=True)
    ap.add_argument("--cert", required=True,
                    help="certification ID to register and bind the account to")
    ap.add_argument("--reviewer", default=None,
                    help="display name; defaults to the username")
    args = ap.parse_args(argv)

    from backend import accounts, attribution, store

    db = store.DB_PATH
    accounts.init(db)

    passphrase = os.environ.get("AXIOM_DEMO_PASSPHRASE")
    if not passphrase:
        first = getpass.getpass("Passphrase for %s: " % args.username)
        again = getpass.getpass("Again: ")
        if first != again:
            print("passphrases do not match", file=sys.stderr)
            return 2
        passphrase = first
    if len(passphrase) < 12:
        print("a demo passphrase must be at least 12 characters", file=sys.stderr)
        return 2

    reviewer = args.reviewer or args.username

    # The per-reviewer HMAC key is only needed so the registry has an entry; the
    # demo does not attest, and printing the key would be the single worst thing
    # this script could do. It is generated, registered, and discarded.
    key = secrets.token_bytes(32)
    try:
        attribution.register(db, reviewer, args.cert, key,
                             note="demo seed %s" % args.cert)
    except ValueError as exc:
        print("registry: %s" % exc, file=sys.stderr)
        return 1
    print("registered   %s under %s (key id %s)"
          % (reviewer, args.cert, attribution.key_id(key)))

    try:
        acct = accounts.enroll(db, args.username, passphrase, args.cert,
                               note="demo account")
    except ValueError as exc:
        print("account: %s" % exc, file=sys.stderr)
        return 1
    print("enrolled     %s as %r under %s" % (acct["username"],
                                              acct["reviewer_name"],
                                              acct["cert_id"]))
    print("\nSign in at POST /api/session with username %r." % args.username)
    return 0


if __name__ == "__main__":
    sys.exit(main())
