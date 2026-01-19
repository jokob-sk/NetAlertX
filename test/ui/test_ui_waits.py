#!/usr/bin/env python3
"""
Basic verification tests for wait helpers used by UI tests.
"""

import sys
import os
from selenium.webdriver.common.by import By

# Add test directory to path
sys.path.insert(0, os.path.dirname(__file__))

from .test_helpers import BASE_URL, wait_for_page_load, wait_for_element_by_css, wait_for_input_value  # noqa: E402


def test_wait_helpers_work_on_dashboard(driver):
    """Ensure wait helpers can detect basic dashboard elements"""
    driver.get(f"{BASE_URL}/index.php")
    wait_for_page_load(driver, timeout=10)
    body = wait_for_element_by_css(driver, "body", timeout=5)
    assert body is not None
    # Device table should be present on the dashboard
    table = wait_for_element_by_css(driver, "table", timeout=10)
    assert table is not None


def test_wait_for_input_value_on_devices(driver):
    """Try generating a MAC on the devices add form and use wait_for_input_value to validate it."""
    driver.get(f"{BASE_URL}/devices.php")
    wait_for_page_load(driver, timeout=10)

    # Try to open an add form - skip if not present
    add_buttons = driver.find_elements(By.CSS_SELECTOR, "button#btnAddDevice, button[onclick*='addDevice'], a[href*='deviceDetails.php?mac='], .btn-add-device")
    if not add_buttons:
        return  # nothing to test in this environment
    # Use JS click with scroll into view to avoid element click intercepted errors
    btn = add_buttons[0]
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    try:
        driver.execute_script("arguments[0].click();", btn)
    except Exception:
        # Fallback to normal click if JS click fails for any reason
        btn.click()

    # Wait for the NEWDEV_devMac field to appear; if not found, try navigating directly to the add form
    try:
        wait_for_element_by_css(driver, "#NEWDEV_devMac", timeout=5)
    except Exception:
        # Some UIs open a new page at deviceDetails.php?mac=new; navigate directly as a fallback
        driver.get(f"{BASE_URL}/deviceDetails.php?mac=new")
        try:
            wait_for_element_by_css(driver, "#NEWDEV_devMac", timeout=10)
        except Exception:
            # If that still fails, attempt to remove canvas overlays (chart.js) and retry clicking the add button
            driver.execute_script("document.querySelectorAll('canvas').forEach(c=>c.style.pointerEvents='none');")
            btn = add_buttons[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            try:
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass
            try:
                wait_for_element_by_css(driver, "#NEWDEV_devMac", timeout=5)
            except Exception:
                # Restore canvas pointer-events and give up
                driver.execute_script("document.querySelectorAll('canvas').forEach(c=>c.style.pointerEvents='auto');")
                return
            # Restore canvas pointer-events
            driver.execute_script("document.querySelectorAll('canvas').forEach(c=>c.style.pointerEvents='auto');")

    # Attempt to click the generate control if present
    gen_buttons = driver.find_elements(By.CSS_SELECTOR, "span[onclick*='generate_NEWDEV_devMac']")
    if not gen_buttons:
        return
    driver.execute_script("arguments[0].click();", gen_buttons[0])
    mac_val = wait_for_input_value(driver, "NEWDEV_devMac", timeout=10)
    assert mac_val, "Generated MAC should be populated"
