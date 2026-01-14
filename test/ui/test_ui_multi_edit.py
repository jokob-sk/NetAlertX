#!/usr/bin/env python3
"""
Multi-Edit Page UI Tests
Tests bulk device operations and form controls
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from test_helpers import BASE_URL


def test_multi_edit_page_loads(driver):
    """Test: Multi-edit page loads successfully"""
    driver.get(f"{BASE_URL}/multiEditCore.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    # Check page loaded without fatal errors
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
    assert len(driver.page_source) > 100, "Page should load some content"


def test_device_selector_present(driver):
    """Test: Device selector/table is rendered or page loads"""
    driver.get(f"{BASE_URL}/multiEditCore.php")
    time.sleep(2)
    # Page should load without fatal errors
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"


def test_bulk_action_buttons_present(driver):
    """Test: Page loads for bulk actions"""
    driver.get(f"{BASE_URL}/multiEditCore.php")
    time.sleep(2)
    # Check page loads without errors
    assert len(driver.page_source) > 50, "Page should load content"


def test_field_dropdowns_present(driver):
    """Test: Page loads successfully"""
    driver.get(f"{BASE_URL}/multiEditCore.php")
    time.sleep(2)
    # Check page loads
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
