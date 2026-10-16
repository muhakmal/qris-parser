#!/usr/bin/env python3
"""Zero-dependency test runner for test_*.py functions."""

import importlib
import inspect
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run() -> int:
    test_files = sorted(Path(__file__).parent.glob("test_*.py"))
    passed = 0
    failed = 0
    print(f"Running test suite across {len(test_files)} test modules...\n")

    for tf in test_files:
        mod_name = f"tests.{tf.stem}"
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            print(f"❌ Failed to import {mod_name}: {e}")
            failed += 1
            continue

        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_"):
                try:
                    fn()
                    passed += 1
                    print(f"  ✅ {mod_name}::{name}")
                except AssertionError as ae:
                    failed += 1
                    print(f"  ❌ {mod_name}::{name} (AssertionError: {ae})")
                except Exception as ex:
                    failed += 1
                    print(f"  ❌ {mod_name}::{name} ({type(ex).__name__}: {ex})")

    print("\n==========================================")
    print(f"Total: {passed + failed} tests | Passed: {passed} | Failed: {failed}")
    print("==========================================")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(run())
