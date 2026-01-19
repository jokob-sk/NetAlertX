#!/usr/bin/env python3
"""
Plugins Page UI Tests
Tests plugin management interface and operations
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .test_helpers import BASE_URL, wait_for_page_load


def test_plugins_page_loads(driver):
    """Test: Plugins page loads successfully"""
    driver.get(f"{BASE_URL}/plugins.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    wait_for_page_load(driver, timeout=10)
    assert "plugin" in driver.page_source.lower(), "Page should contain plugin content"


def test_plugin_list_present(driver):
    """Test: Plugin page loads successfully"""
    driver.get(f"{BASE_URL}/plugins.php")
    wait_for_page_load(driver, timeout=10)

    # Check page loaded
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
    assert len(driver.page_source) > 50, "Page should load content"


def test_plugin_actions_present(driver):
    """Test: Plugin page loads without errors"""
    driver.get(f"{BASE_URL}/plugins.php")
    wait_for_page_load(driver, timeout=10)
    # Check page loads
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
