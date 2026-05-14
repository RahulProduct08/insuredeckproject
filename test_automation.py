"""
Test script for Time Tracker Automation
Validates configuration and tests connectivity
"""

import json
from pathlib import Path
from time_tracker_automation import TimeTrackerAutomation

def test_config():
    """Test configuration file"""
    print("=" * 50)
    print("Testing Time Tracker Configuration")
    print("=" * 50)

    try:
        automation = TimeTrackerAutomation()
        config = automation.config

        print("[OK] Config file loaded successfully")
        print()

        # Validate required fields
        required_fields = {
            'ems_config': ['url', 'username', 'password'],
            'defaults': ['customer', 'project', 'date'],
            'daily_entries': []
        }

        for section, fields in required_fields.items():
            if section not in config:
                print(f"[ERROR] Missing section: {section}")
                return False

            if isinstance(fields, list) and fields:
                for field in fields:
                    if field not in config[section]:
                        print(f"[ERROR] Missing field: {section}.{field}")
                        return False

        print("[OK] All required config sections present")
        print()

        # Check EMS Config
        print("EMS Configuration:")
        print(f"  URL: {config['ems_config']['url']}")
        print(f"  Username: {config['ems_config']['username']}")
        print(f"  Password: {'*' * len(config['ems_config']['password'])} (hidden)")
        print()

        # Check Defaults
        print("Default Values:")
        print(f"  Customer: {config['defaults']['customer']}")
        print(f"  Project: {config['defaults']['project']}")
        print()

        # Check Entries
        entries = config['daily_entries']
        total_hours = sum(e['hours'] for e in entries)

        print(f"Daily Entries ({len(entries)} tickets):")
        for entry in entries:
            print(f"  {entry['ticket']} - {entry['hours']}h ({entry['work_type']})")
        print()
        print(f"Total Hours: {total_hours}h")

        if total_hours != 10:
            print(f"[WARNING] Total hours is {total_hours}, expected 10")

        print()
        print("[OK] Configuration validated successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Configuration test failed: {e}")
        return False

def test_webdriver():
    """Test WebDriver setup"""
    print()
    print("=" * 50)
    print("Testing WebDriver Setup")
    print("=" * 50)

    try:
        automation = TimeTrackerAutomation()
        automation.setup_driver()
        print("[OK] WebDriver initialized successfully")

        # Test navigation
        automation.driver.get("https://www.google.com")
        print("[OK] Successfully navigated to test URL")

        automation.close_driver()
        print("[OK] WebDriver closed successfully")
        return True

    except Exception as e:
        print(f"[ERROR] WebDriver test failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure Chrome browser is installed")
        print("  2. Run: pip install webdriver-manager")
        print("  3. Check firewall/proxy settings")
        return False

def main():
    """Run all tests"""
    print()
    print("Time Tracker Automation - Test Suite")
    print()

    tests = [
        ("Configuration", test_config),
        ("WebDriver", test_webdriver),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[✗] {test_name} test error: {e}")
            results.append((test_name, False))

    print()
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "OK" if result else "FAIL"
        print(f"[{symbol}] {test_name}: {status}")

    all_passed = all(result for _, result in results)
    print()

    if all_passed:
        print("[OK] All tests passed! Ready to run automation.")
        print()
        print("Next: python time_tracker_automation.py")
    else:
        print("[ERROR] Some tests failed. Check configuration and try again.")

    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
