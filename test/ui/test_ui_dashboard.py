#!/usr/bin/env python3
"""
Dashboard Page UI Tests
Tests main dashboard metrics, charts, and device table
"""

import sys
import os

from selenium.webdriver.common.by import By

# Add test directory to path
sys.path.insert(0, os.path.dirname(__file__))

from .test_helpers import BASE_URL, wait_for_page_load, wait_for_element_by_css  # noqa: E402


def test_dashboard_loads(driver):
    """Test: Dashboard/index page loads successfully"""
    driver.get(f"{BASE_URL}/index.php")
    wait_for_page_load(driver, timeout=10)
    assert driver.title, "Page should have a title"


def test_metric_tiles_present(driver):
    """Test: Dashboard metric tiles are rendered"""
    driver.get(f"{BASE_URL}/index.php")
    wait_for_page_load(driver, timeout=10)
    # Wait for at least one metric/tile/info-box to be present
    wait_for_element_by_css(driver, ".metric, .tile, .info-box, .small-box", timeout=10)
    tiles = driver.find_elements(By.CSS_SELECTOR, ".metric, .tile, .info-box, .small-box")
    assert len(tiles) > 0, "Dashboard should have metric tiles"


def test_device_table_present(driver):
    """Test: Dashboard device table is rendered"""
    driver.get(f"{BASE_URL}/index.php")
    wait_for_page_load(driver, timeout=10)
    wait_for_element_by_css(driver, "table", timeout=10)
    table = driver.find_elements(By.CSS_SELECTOR, "table")
    assert len(table) > 0, "Dashboard should have a device table"


def test_charts_present(driver):
    """Test: Dashboard charts are rendered"""
    driver.get(f"{BASE_URL}/index.php")
    wait_for_page_load(driver, timeout=15)  # Charts may take longer to load
    wait_for_element_by_css(driver, "canvas, .chart, svg", timeout=15)
    charts = driver.find_elements(By.CSS_SELECTOR, "canvas, .chart, svg")
    assert len(charts) > 0, "Dashboard should have charts"
