#!/usr/bin/env python3
"""
Settings Page UI Tests
Tests settings page load, settings groups, and configuration
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from test_helpers import BASE_URL


def test_settings_page_loads(driver):
    """Test: Settings page loads successfully"""
    driver.get(f"{BASE_URL}/settings.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    assert "setting" in driver.page_source.lower(), "Page should contain settings content"


def test_settings_groups_present(driver):
    """Test: Settings groups/sections are rendered"""
    driver.get(f"{BASE_URL}/settings.php")
    time.sleep(2)
    groups = driver.find_elements(By.CSS_SELECTOR, ".settings-group, .panel, .card, fieldset")
    assert len(groups) > 0, "Settings groups should be present"


def test_settings_inputs_present(driver):
    """Test: Settings input fields are rendered"""
    driver.get(f"{BASE_URL}/settings.php")
    time.sleep(2)
    inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
    assert len(inputs) > 0, "Settings input fields should be present"


def test_save_button_present(driver):
    """Test: Save button is visible"""
    driver.get(f"{BASE_URL}/settings.php")
    time.sleep(2)
    save_btn = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button#save, .btn-save")
    assert len(save_btn) > 0, "Save button should be present"


# Settings endpoint doesn't exist in Flask API - settings are managed via PHP/config files
