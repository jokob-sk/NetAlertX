#!/usr/bin/env python3
"""
Dashboard Page UI Tests
Tests main dashboard metrics, charts, and device table
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

import sys
import os

# Add test directory to path
sys.path.insert(0, os.path.dirname(__file__))

from test_helpers import BASE_URL   # noqa: E402 [flake8 lint suppression]


@pytest.mark.ui
def test_dashboard_loads(driver):
    """Test: Dashboard/index page loads successfully"""
    driver.get(f"{BASE_URL}/index.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    assert driver.title, "Page should have a title"


@pytest.mark.ui
def test_metric_tiles_present(driver):
    """Test: Dashboard metric tiles are rendered"""
    driver.get(f"{BASE_URL}/index.php")
    time.sleep(2)
    tiles = driver.find_elements(By.CSS_SELECTOR, ".metric, .tile, .info-box, .small-box")
    assert len(tiles) > 0, "Dashboard should have metric tiles"


@pytest.mark.ui
def test_device_table_present(driver):
    """Test: Dashboard device table is rendered"""
    driver.get(f"{BASE_URL}/index.php")
    time.sleep(2)
    table = driver.find_elements(By.CSS_SELECTOR, "table")
    assert len(table) > 0, "Dashboard should have a device table"


@pytest.mark.ui
def test_charts_present(driver):
    """Test: Dashboard charts are rendered"""
    driver.get(f"{BASE_URL}/index.php")
    time.sleep(3)  # Charts may take longer to load
    charts = driver.find_elements(By.CSS_SELECTOR, "canvas, .chart, svg")
    assert len(charts) > 0, "Dashboard should have charts"
