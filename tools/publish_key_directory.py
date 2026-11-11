#!/usr/bin/env python3
"""
Build and sign the reviewer key directory.

Usage:
    python3 tools/publish_key_directory.py --key out/export.key \
        --out out/key-directory.json

This runs on the Platform host, where the registry lives. It refuses to build
if the registry chain does not verify — a directory published from a broken
chain would carry bindings nobody should trust.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import key_directory, store


def main(argv=None):
    p = argparse.ArgumentParser(description="Build and sign the key directory.")
    p.add_argument("--key", required=True, help="32-byte export key file")
    p.add_argument("--out", required=True, help="where to write the directory")
    a = p.parse_args(argv)

    with open(a.key, "rb") as f:
        key = f.read()
    if len(key) != 32:
        print("the export key must be exactly 32 raw bytes, got %d" % len(key),
              file=sys.stderr)
        return 2

    try:
        body = key_directory.build(store.DB_PATH)
    except ValueError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1

    signed = key_directory.sign(body, key)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    key_directory.save(signed, a.out)

    print("wrote %s" % a.out)
    print("  %d binding(s), signed with key %s" %
          (len(body["entries"]), signed["signature"]["key_id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
