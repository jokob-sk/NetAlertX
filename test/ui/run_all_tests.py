#!/usr/bin/env python3
"""
NetAlertX UI Test Runner
Runs all page-specific UI tests and provides summary
"""

import sys
import os
import pytest


def main():
    """Run all UI tests and provide summary"""
    print("\n" + "=" * 70)
    print("NetAlertX UI Test Suite")
    print("=" * 70)

    # Get directory of this script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    test_modules = [
        ("Dashboard", "test_ui_dashboard.py"),
        ("Devices", "test_ui_devices.py"),
        ("Network", "test_ui_network.py"),
        ("Maintenance", "test_ui_maintenance.py"),
        ("Multi-Edit", "test_ui_multi_edit.py"),
        ("Notifications", "test_ui_notifications.py"),
        ("Settings", "test_ui_settings.py"),
        ("Plugins", "test_ui_plugins.py"),
    ]

    results = {}

    for name, filename in test_modules:
        try:
            print(f"\nRunning {name} tests...")
            file_path = os.path.join(base_dir, filename)
            # Run pytest
            result = pytest.main([file_path, "-v"])
            results[name] = result == 0
        except Exception as e:
            print(f"\n✗ {name} tests failed with exception: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70 + "\n")

    for name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\nOverall: {passed}/{total} test suites passed\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
