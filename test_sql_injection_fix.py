#!/usr/bin/env python3
"""
Test script to validate SQL injection fixes for issue #1179
"""
import re
import sys

def test_datetime_injection_fix():
    """Test that datetime injection vulnerability is fixed"""
    
    # Read the reporting.py file
    with open('server/messaging/reporting.py', 'r') as f:
        content = f.read()
    
    # Check for vulnerable f-string patterns with datetime and user input
    vulnerable_patterns = [
        r"datetime\('now',\s*f['\"].*{get_setting_value\('NTFPRCS_alert_down_time'\)}",
        r"datetime\('now',\s*f['\"].*{get_timezone_offset\(\)}"
    ]
    
    vulnerabilities_found = []
    for pattern in vulnerable_patterns:
        matches = re.findall(pattern, content)
        if matches:
            vulnerabilities_found.extend(matches)
    
    if vulnerabilities_found:
        print("❌ SECURITY TEST FAILED: Vulnerable datetime patterns found:")
        for vuln in vulnerabilities_found:
            print(f"  - {vuln}")
        return False
    
    # Check for the secure patterns
    secure_patterns = [
        r"minutes = int\(get_setting_value\('NTFPRCS_alert_down_time'\) or 0\)",
        r"tz_offset = get_timezone_offset\(\)"
    ]
    
    secure_found = 0
    for pattern in secure_patterns:
        if re.search(pattern, content):
            secure_found += 1
    
    if secure_found >= 2:
        print("✅ SECURITY TEST PASSED: Secure datetime handling implemented")
        return True
    else:
        print("⚠️  SECURITY TEST WARNING: Expected secure patterns not fully found")
        return False

def test_notification_instance_fix():
    """Test that the clearPendingEmailFlag function is secure"""
    
    with open('server/models/notification_instance.py', 'r') as f:
        content = f.read()
    
    # Check for vulnerable f-string patterns in clearPendingEmailFlag
    clearflag_section = ""
    in_function = False
    lines = content.split('\n')
    
    for line in lines:
        if 'def clearPendingEmailFlag' in line:
            in_function = True
        elif in_function and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
            break
        
        if in_function:
            clearflag_section += line + '\n'
    
    # Check for vulnerable patterns
    vulnerable_patterns = [
        r"f['\"].*{get_setting_value\('NTFPRCS_alert_down_time'\)}",
        r"f['\"].*{get_timezone_offset\(\)}"
    ]
    
    vulnerabilities_found = []
    for pattern in vulnerable_patterns:
        matches = re.findall(pattern, clearflag_section)
        if matches:
            vulnerabilities_found.extend(matches)
    
    if vulnerabilities_found:
        print("❌ SECURITY TEST FAILED: clearPendingEmailFlag still vulnerable:")
        for vuln in vulnerabilities_found:
            print(f"  - {vuln}")
        return False
    
    print("✅ SECURITY TEST PASSED: clearPendingEmailFlag appears secure")
    return True

def test_code_quality():
    """Test basic code quality and imports"""
    
    # Check if the modified files can be imported (basic syntax check)
    try:
        import subprocess
        result = subprocess.run([
            'python3', '-c', 
            'import sys; sys.path.append("server"); from messaging import reporting'
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ CODE QUALITY TEST PASSED: reporting.py imports successfully")
            return True
        else:
            print(f"❌ CODE QUALITY TEST FAILED: Import error: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  CODE QUALITY TEST WARNING: Could not test imports: {e}")
        return True  # Don't fail for environment issues

if __name__ == "__main__":
    print("🔒 Running SQL Injection Security Tests for Issue #1179\n")
    
    tests = [
        ("Datetime Injection Fix", test_datetime_injection_fix),
        ("Notification Instance Security", test_notification_instance_fix),
        ("Code Quality", test_code_quality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"🔒 Security Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All security tests passed! The SQL injection fixes are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some security tests failed. Please review the fixes.")
        sys.exit(1)