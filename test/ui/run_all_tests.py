#!/usr/bin/env python3
"""
NetAlertX UI Test Runner
Runs all page-specific UI tests and provides summary
"""

import sys
import os

# Add test directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import all test modules
import test_ui_dashboard  # noqa: E402 [flake8 lint suppression]
import test_ui_devices  # noqa: E402 [flake8 lint suppression]
import test_ui_network  # noqa: E402 [flake8 lint suppression]
import test_ui_maintenance  # noqa: E402 [flake8 lint suppression]
import test_ui_multi_edit  # noqa: E402 [flake8 lint suppression]
import test_ui_notifications  # noqa: E402 [flake8 lint suppression]
import test_ui_settings  # noqa: E402 [flake8 lint suppression]
import test_ui_plugins  # noqa: E402 [flake8 lint suppression]


def main():
    """Run all UI tests and provide summary"""
    print("\n" + "=" * 70)
    print("NetAlertX UI Test Suite")
    print("=" * 70)

    test_modules = [
        ("Dashboard", test_ui_dashboard),
        ("Devices", test_ui_devices),
        ("Network", test_ui_network),
        ("Maintenance", test_ui_maintenance),
        ("Multi-Edit", test_ui_multi_edit),
        ("Notifications", test_ui_notifications),
        ("Settings", test_ui_settings),
        ("Plugins", test_ui_plugins),
    ]

    results = {}

    for name, module in test_modules:
        try:
            result = module.run_tests()
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
