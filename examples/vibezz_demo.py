#!/usr/bin/env python3
"""
Vibezz Demo - Example usage of the enhanced Python debugger
"""

import sys
import types
import importlib
from vibethon.vibezz import vibezz_debugger

def main():
    print("🚀 Starting Vibezz - Enhanced Python Debugger")
    print("=" * 50)

    print("\n" + "=" * 50)
    print("🎯 Running test functions...")
    print("=" * 50)
    
    # ------------------------------------------------------------
    # Dynamically load demo functions from ``no_exceptions_only_vibes``
    # ------------------------------------------------------------

    try:
        vibes_mod = importlib.import_module("no_exceptions_only_vibes")
    except ModuleNotFoundError:
        print("❌ Module 'no_exceptions_only_vibes' not found. Aborting.")
        sys.exit(1)

    # Instrument functions inside that module so our debugger hooks are active
    vibezz_debugger.auto_instrument(module_globals=vibes_mod.__dict__)

    # Collect all user-defined functions (skip private/dunder)
    tests = [
        (name, obj) for name, obj in vibes_mod.__dict__.items()
        if isinstance(obj, types.FunctionType) and not name.startswith("__")
    ]

    if not tests:
        print("⚠️  No callable functions found in 'no_exceptions_only_vibes'. Nothing to run.")
        sys.exit(0)

    # ---- Allow selection of a subset of tests by index (1-based) ----
    # Specify the indices of the tests you want to run (1-based)
    SELECTED_TEST_INDICES = [0,6,10]  # <-- Change this list to select which tests to run

    # Filter the tests list to only include the selected indices
    selected_tests = [
        tests[i - 1] for i in SELECTED_TEST_INDICES
        if 1 <= i <= len(tests)
    ]

    if not selected_tests:
        print("⚠️  No tests selected. Please update SELECTED_TEST_INDICES.")
        sys.exit(0)

    passed, failed = 0, 0

    for idx, (name, fn) in enumerate(selected_tests, 1):
        print(f"\n{idx}. Testing {name}() ...")
        try:
            result = fn()
            print(f"✅ {name} executed successfully – return value: {result}")
            passed += 1
        except Exception as e:
            print(f"❌ {name} raised an exception: {e}")
            import traceback; traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test summary: {passed} passed / {passed + failed} total")

    if failed == 0:
        print("🎉 All functions executed without unhandled exceptions!")
    else:
        print("⚠️  Some functions failed – see details above.")

    print("\n✅ Vibezz debugging session complete!")

if __name__ == "__main__":
    main() 