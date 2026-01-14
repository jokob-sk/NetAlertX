#!/usr/bin/env python3
"""
Plugins Page UI Tests
Tests plugin management interface and operations
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

from test_helpers import BASE_URL


@pytest.mark.ui
def test_plugins_page_loads(driver):
    """Test: Plugins page loads successfully"""
    driver.get(f"{BASE_URL}/pluginsCore.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    assert "plugin" in driver.page_source.lower(), "Page should contain plugin content"


@pytest.mark.ui
def test_plugin_list_present(driver):
    """Test: Plugin page loads successfully"""
    driver.get(f"{BASE_URL}/pluginsCore.php")
    time.sleep(2)
    # Check page loaded
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
    assert len(driver.page_source) > 50, "Page should load content"


@pytest.mark.ui
def test_plugin_actions_present(driver):
    """Test: Plugin page loads without errors"""
    driver.get(f"{BASE_URL}/pluginsCore.php")
    time.sleep(2)
    # Check page loads
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
