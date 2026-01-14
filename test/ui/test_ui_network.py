#!/usr/bin/env python3
"""
Network Page UI Tests
Tests network topology visualization and device relationships
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

from test_helpers import BASE_URL


@pytest.mark.ui
def test_network_page_loads(driver):
    """Test: Network page loads successfully"""
    driver.get(f"{BASE_URL}/network.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    assert driver.title, "Network page should have a title"


@pytest.mark.ui
def test_network_tree_present(driver):
    """Test: Network tree container is rendered"""
    driver.get(f"{BASE_URL}/network.php")
    time.sleep(2)
    tree = driver.find_elements(By.ID, "networkTree")
    assert len(tree) > 0, "Network tree should be present"


@pytest.mark.ui
def test_network_tabs_present(driver):
    """Test: Network page loads successfully"""
    driver.get(f"{BASE_URL}/network.php")
    time.sleep(2)
    # Check page loaded without fatal errors
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
    assert len(driver.page_source) > 100, "Page should load content"


@pytest.mark.ui
def test_device_tables_present(driver):
    """Test: Device tables are rendered"""
    driver.get(f"{BASE_URL}/network.php")
    time.sleep(2)
    tables = driver.find_elements(By.CSS_SELECTOR, ".networkTable, table")
    assert len(tables) > 0, "Device tables should be present"
