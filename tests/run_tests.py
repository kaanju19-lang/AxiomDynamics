"""
Zero-dependency test runner. If you have pytest, just run `pytest tests/` --
it understands these plain-assert test functions fine. This script exists
for the air-gapped case where even pytest isn't installed: it only needs
numpy (already required by the app) and the standard library.

Usage: python3 tests/run_tests.py
"""
import importlib.util
import os
import sys
import traceback

TEST_FILE = os.path.join(os.path.dirname(__file__), "test_physics.py")


def main():
    spec = importlib.util.spec_from_file_location("test_physics", TEST_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tests = [getattr(mod, n) for n in dir(mod) if n.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
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
