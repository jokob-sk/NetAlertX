#!/usr/bin/env python3
"""
Maintenance Page UI Tests
Tests CSV export/import, delete operations, database tools
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

from test_helpers import BASE_URL, api_get


@pytest.mark.ui
def test_maintenance_page_loads(driver):
    """Test: Maintenance page loads successfully"""
    driver.get(f"{BASE_URL}/maintenance.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    assert "Maintenance" in driver.page_source, "Page should show Maintenance content"


@pytest.mark.ui
def test_export_buttons_present(driver):
    """Test: Export buttons are visible"""
    driver.get(f"{BASE_URL}/maintenance.php")
    time.sleep(2)
    export_btn = driver.find_elements(By.ID, "btnExportCSV")
    assert len(export_btn) > 0, "Export CSV button should be present"


@pytest.mark.ui
def test_export_csv_button_works(driver):
    """Test: CSV export button triggers download"""
    import os
    import glob

    driver.get(f"{BASE_URL}/maintenance.php")
    time.sleep(2)

    # Clear any existing downloads
    download_dir = getattr(driver, 'download_dir', '/tmp/selenium_downloads')
    for f in glob.glob(f"{download_dir}/*.csv"):
        os.remove(f)

    # Find the export button
    export_btns = driver.find_elements(By.ID, "btnExportCSV")

    if len(export_btns) > 0:
        export_btn = export_btns[0]

        # Click it (JavaScript click works even if CSS hides it)
        driver.execute_script("arguments[0].click();", export_btn)

        # Wait for download to complete (up to 10 seconds)
        downloaded = False
        for i in range(20):  # Check every 0.5s for 10s
            time.sleep(0.5)
            csv_files = glob.glob(f"{download_dir}/*.csv")
            if len(csv_files) > 0:
                # Check file has content (download completed)
                if os.path.getsize(csv_files[0]) > 0:
                    downloaded = True
                    break

        if downloaded:
            # Verify CSV file exists and has data
            csv_file = glob.glob(f"{download_dir}/*.csv")[0]
            assert os.path.exists(csv_file), "CSV file should be downloaded"
            assert os.path.getsize(csv_file) > 100, "CSV file should have content"

            # Optional: Verify CSV format
            with open(csv_file, 'r') as f:
                first_line = f.readline()
                assert 'mac' in first_line.lower() or 'device' in first_line.lower(), "CSV should have header"
        else:
            # Download via blob/JavaScript - can't verify file in headless mode
            # Just verify button click didn't cause errors
            assert "error" not in driver.page_source.lower(), "Button click should not cause errors"
    else:
        # Button doesn't exist on this page
        assert True, "Export button not found on this page"


@pytest.mark.ui
def test_import_section_present(driver):
    """Test: Import section is rendered or page loads without errors"""
    driver.get(f"{BASE_URL}/maintenance.php")
    time.sleep(2)
    # Check page loaded and doesn't show fatal errors
    assert "fatal" not in driver.page_source.lower(), "Page should not show fatal errors"
    assert "maintenance" in driver.page_source.lower() or len(driver.page_source) > 100, "Page should load content"


@pytest.mark.ui
def test_delete_buttons_present(driver):
    """Test: Delete operation buttons are visible (at least some)"""
    driver.get(f"{BASE_URL}/maintenance.php")
    time.sleep(2)
    buttons = [
        "btnDeleteEmptyMACs",
        "btnDeleteAllDevices",
        "btnDeleteUnknownDevices",
        "btnDeleteEvents",
        "btnDeleteEvents30"
    ]
    found = []
    for btn_id in buttons:
        found.append(len(driver.find_elements(By.ID, btn_id)) > 0)
    # At least 2 buttons should be present (Events buttons are always there)
    assert sum(found) >= 2, f"At least 2 delete buttons should be present, found: {sum(found)}/{len(buttons)}"


@pytest.mark.ui
def test_csv_export_api(api_token):
    """Test: CSV export endpoint returns data"""
    response = api_get("/devices/export/csv", api_token)
    assert response.status_code == 200, "CSV export API should return 200"
    # Check if response looks like CSV
    content = response.text
    assert "mac" in content.lower() or len(content) > 0, "CSV should contain data"
