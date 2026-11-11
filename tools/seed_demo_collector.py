#!/usr/bin/env python3
"""
Enroll a demo collector for the ingest endpoint.

Usage:
    python3 -m tools.seed_demo_collector "detector-1" "Wayside detector, milepost 100"

This is an administrative action. The token is returned once and must be saved
by the operator. If lost, enrollment must be revoked and a new one created.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import ingest_auth, store


def main(argv):
    if len(argv) < 2:
        print("Usage: %s <name> [note]" % argv[0], file=sys.stderr)
        return 1
    name = argv[1]
    note = argv[2] if len(argv) > 2 else ""
    try:
        result = ingest_auth.enroll_collector(store.DB_PATH, name, note=note)
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1
    print("=" * 62)
    print("Collector enrolled")
    print("=" * 62)
    print("ID:    %s" % result["id"])
    print("Name:  %s" % result["name"])
    print("Time:  %s" % result["created_at"])
    print()
    print("BEARER TOKEN - save this securely; it is not shown again:")
    print(result["token"])
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
