"""
Zero-dependency test runner. If you have pytest, just run `pytest tests/` --
it understands these plain-assert test functions fine. This script exists
for the air-gapped case where even pytest isn't installed: it only needs
numpy (already required by the app) and the standard library.

Discovers every `test_*.py` in this directory, so a new test module is picked
up without editing this file. Running it twice is safe: each module imports
from the top, and test_store points the database at a throwaway file.

Usage: python3 tests/run_tests.py
"""
import glob
import importlib.util
import os
import sys
import traceback

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    files = sorted(glob.glob(os.path.join(TESTS_DIR, "test_*.py")))
    if not files:
        print("no test files found")
        return 1

    passed, failed = 0, 0
    for path in files:
        label = os.path.basename(path)
        print(f"\n== {label} " + "=" * max(0, 60 - len(label)))
        try:
            mod = _load(path)
        except Exception as e:  # a module that will not import is a failure, not a skip
            print(f"FAIL  <import {label}> -> {e}")
            traceback.print_exc()
            failed += 1
            continue

        tests = [getattr(mod, n) for n in dir(mod) if n.startswith("test_")]
        for t in tests:
            if not callable(t):
                continue
            try:
                t()
                print(f"PASS  {t.__name__}")
                passed += 1
            except Exception as e:
                print(f"FAIL  {t.__name__} -> {e}")
                traceback.print_exc()
                failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
