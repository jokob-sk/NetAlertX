#!/usr/bin/env python3
"""
Test Chromium availability and setup
"""
import os
import subprocess

# Check if chromium and chromedriver are installed
chromium_paths = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']
chromedriver_paths = ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']

print("=== Checking for Chromium ===")
for path in chromium_paths:
    if os.path.exists(path):
        print(f"✓ Found: {path}")
        result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
        print(f"  Version: {result.stdout.strip()}")
    else:
        print(f"✗ Not found: {path}")

print("\n=== Checking for chromedriver ===")
for path in chromedriver_paths:
    if os.path.exists(path):
        print(f"✓ Found: {path}")
        result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
        print(f"  Version: {result.stdout.strip()}")
    else:
        print(f"✗ Not found: {path}")

# Try to import selenium and create a driver
print("\n=== Testing Selenium Driver Creation ===")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    # Find chromium
    chromium = None
    for path in chromium_paths:
        if os.path.exists(path):
            chromium = path
            break

    # Find chromedriver
    chromedriver = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            chromedriver = path
            break

    if chromium and chromedriver:
        chrome_options.binary_location = chromium
        service = Service(chromedriver)
        print("Attempting to create driver with:")
        print(f"  Chromium: {chromium}")
        print(f"  Chromedriver: {chromedriver}")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Driver created successfully!")
        driver.quit()
        print("✓ Driver closed successfully!")
    else:
        print(f"✗ Missing binaries - chromium: {chromium}, chromedriver: {chromedriver}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
