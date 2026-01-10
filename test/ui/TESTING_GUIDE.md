# UI Testing Guide

## Overview
This directory contains Selenium-based UI tests for NetAlertX. Tests validate both API endpoints and browser functionality.

## Test Types

### 1. Page Load Tests (Basic)
```python
def test_page_loads(driver):
    """Test: Page loads without errors"""
    driver.get(f"{BASE_URL}/page.php")
    time.sleep(2)
    assert "fatal" not in driver.page_source.lower()
```

### 2. Element Presence Tests
```python
def test_button_present(driver):
    """Test: Button exists on page"""
    driver.get(f"{BASE_URL}/page.php")
    time.sleep(2)
    button = driver.find_element(By.ID, "myButton")
    assert button.is_displayed(), "Button should be visible"
```

### 3. Functional Tests (Button Clicks)
```python
def test_button_click_works(driver):
    """Test: Button click executes action"""
    driver.get(f"{BASE_URL}/page.php")
    time.sleep(2)

    # Find button
    button = driver.find_element(By.ID, "myButton")

    # Verify it's clickable
    assert button.is_enabled(), "Button should be enabled"

    # Click it
    button.click()

    # Wait for result
    time.sleep(1)

    # Verify action happened (check for success message, modal, etc.)
    success_msg = driver.find_elements(By.CSS_SELECTOR, ".alert-success")
    assert len(success_msg) > 0, "Success message should appear"
```

### 4. Form Input Tests
```python
def test_form_submission(driver):
    """Test: Form accepts input and submits"""
    driver.get(f"{BASE_URL}/form.php")
    time.sleep(2)

    # Fill form fields
    name_field = driver.find_element(By.ID, "deviceName")
    name_field.clear()
    name_field.send_keys("Test Device")

    # Select dropdown
    from selenium.webdriver.support.select import Select
    dropdown = Select(driver.find_element(By.ID, "deviceType"))
    dropdown.select_by_visible_text("Router")

    # Click submit
    submit_btn = driver.find_element(By.ID, "btnSave")
    submit_btn.click()

    time.sleep(2)

    # Verify submission
    assert "success" in driver.page_source.lower()
```

### 5. AJAX/Fetch Tests
```python
def test_ajax_request(driver):
    """Test: AJAX request completes successfully"""
    driver.get(f"{BASE_URL}/page.php")
    time.sleep(2)

    # Click button that triggers AJAX
    ajax_btn = driver.find_element(By.ID, "loadData")
    ajax_btn.click()

    # Wait for AJAX to complete (look for loading indicator to disappear)
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element((By.CLASS_NAME, "spinner"))
    )

    # Verify data loaded
    data_table = driver.find_element(By.ID, "dataTable")
    assert len(data_table.text) > 0, "Data should be loaded"
```

### 6. API Endpoint Tests
```python
def test_api_endpoint(api_token):
    """Test: API endpoint returns correct data"""
    response = api_get("/devices", api_token)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["results"]) > 0
```

### 7. Multi-Step Workflow Tests
```python
def test_device_edit_workflow(driver):
    """Test: Complete device edit workflow"""
    # Step 1: Navigate to devices page
    driver.get(f"{BASE_URL}/devices.php")
    time.sleep(2)

    # Step 2: Click first device
    first_device = driver.find_element(By.CSS_SELECTOR, "table tbody tr:first-child a")
    first_device.click()
    time.sleep(2)

    # Step 3: Edit device name
    name_field = driver.find_element(By.ID, "deviceName")
    original_name = name_field.get_attribute("value")
    name_field.clear()
    name_field.send_keys("Updated Name")

    # Step 4: Save changes
    save_btn = driver.find_element(By.ID, "btnSave")
    save_btn.click()
    time.sleep(2)

    # Step 5: Verify save succeeded
    assert "success" in driver.page_source.lower()

    # Step 6: Restore original name
    name_field = driver.find_element(By.ID, "deviceName")
    name_field.clear()
    name_field.send_keys(original_name)
    save_btn = driver.find_element(By.ID, "btnSave")
    save_btn.click()
```

## Common Selenium Patterns

### Finding Elements
```python
# By ID (fastest, most reliable)
element = driver.find_element(By.ID, "myButton")

# By CSS selector (flexible)
element = driver.find_element(By.CSS_SELECTOR, ".btn-primary")
elements = driver.find_elements(By.CSS_SELECTOR, "table tr")

# By XPath (powerful but slow)
element = driver.find_element(By.XPATH, "//button[@type='submit']")

# By link text
element = driver.find_element(By.LINK_TEXT, "Edit Device")

# By partial link text
element = driver.find_element(By.PARTIAL_LINK_TEXT, "Edit")

# Check if element exists (don't fail if missing)
elements = driver.find_elements(By.ID, "optional_element")
if len(elements) > 0:
    elements[0].click()
```

### Waiting for Elements
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Wait up to 10 seconds for element to be present
element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "myElement"))
)

# Wait for element to be clickable
element = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "myButton"))
)

# Wait for element to disappear
WebDriverWait(driver, 10).until(
    EC.invisibility_of_element((By.CLASS_NAME, "loading-spinner"))
)

# Wait for text to be present
WebDriverWait(driver, 10).until(
    EC.text_to_be_present_in_element((By.ID, "status"), "Complete")
)
```

### Interacting with Elements
```python
# Click
button.click()

# Type text
input_field.send_keys("Hello World")

# Clear and type
input_field.clear()
input_field.send_keys("New Text")

# Get text
text = element.text

# Get attribute
value = input_field.get_attribute("value")
href = link.get_attribute("href")

# Check visibility
if element.is_displayed():
    element.click()

# Check if enabled
if button.is_enabled():
    button.click()

# Check if selected (checkboxes/radio)
if checkbox.is_selected():
    checkbox.click()  # Uncheck it
```

### Handling Alerts/Modals
```python
# Wait for alert
WebDriverWait(driver, 5).until(EC.alert_is_present())

# Accept alert (click OK)
alert = driver.switch_to.alert
alert.accept()

# Dismiss alert (click Cancel)
alert.dismiss()

# Get alert text
alert_text = alert.text

# Bootstrap modals
modal = driver.find_element(By.ID, "myModal")
assert modal.is_displayed(), "Modal should be visible"
```

### Handling Dropdowns
```python
from selenium.webdriver.support.select import Select

# Select by visible text
dropdown = Select(driver.find_element(By.ID, "myDropdown"))
dropdown.select_by_visible_text("Option 1")

# Select by value
dropdown.select_by_value("option1")

# Select by index
dropdown.select_by_index(0)

# Get selected option
selected = dropdown.first_selected_option
print(selected.text)

# Get all options
all_options = dropdown.options
for option in all_options:
    print(option.text)
```

## Running Tests

### Run all tests
```bash
pytest test/ui/
```

### Run specific test file
```bash
pytest test/ui/test_ui_dashboard.py
```

### Run specific test
```bash
pytest test/ui/test_ui_dashboard.py::test_dashboard_loads
```

### Run with verbose output
```bash
pytest test/ui/ -v
```

### Run with very verbose output (show page source on failures)
```bash
pytest test/ui/ -vv
```

### Run and stop on first failure
```bash
pytest test/ui/ -x
```

## Best Practices

1. **Use explicit waits** instead of `time.sleep()` when possible
2. **Test the behavior, not implementation** - focus on what users see/do
3. **Keep tests independent** - each test should work alone
4. **Clean up after tests** - reset any changes made during testing
5. **Use descriptive test names** - `test_export_csv_button_downloads_file` not `test_1`
6. **Add docstrings** - explain what each test validates
7. **Test error cases** - not just happy paths
8. **Use CSS selectors over XPath** when possible (faster, more readable)
9. **Group related tests** - keep page-specific tests in same file
10. **Avoid hardcoded waits** - use WebDriverWait with conditions

## Debugging Failed Tests

### Take screenshot on failure
```python
try:
    assert something
except AssertionError:
    driver.save_screenshot("/tmp/test_failure.png")
    raise
```

### Print page source
```python
print(driver.page_source)
```

### Print current URL
```python
print(driver.current_url)
```

### Check console logs (JavaScript errors)
```python
logs = driver.get_log('browser')
for log in logs:
    print(log)
```

### Run in non-headless mode (see what's happening)
Modify `test_helpers.py`:
```python
# Comment out this line:
# chrome_options.add_argument('--headless=new')
```

## Example: Complete Functional Test

```python
def test_device_delete_workflow(driver, api_token):
    """Test: Complete device deletion workflow"""
    # Setup: Create a test device via API
    import requests
    headers = {"Authorization": f"Bearer {api_token}"}
    test_device = {
        "mac": "00:11:22:33:44:55",
        "name": "Test Device",
        "type": "Other"
    }
    create_response = requests.post(
        f"{API_BASE_URL}/device",
        headers=headers,
        json=test_device
    )
    assert create_response.status_code == 200

    # Navigate to devices page
    driver.get(f"{BASE_URL}/devices.php")
    time.sleep(2)

    # Search for the test device
    search_box = driver.find_element(By.CSS_SELECTOR, ".dataTables_filter input")
    search_box.send_keys("Test Device")
    time.sleep(1)

    # Click delete button for the device
    delete_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-delete")
    delete_btn.click()

    # Confirm deletion in modal
    time.sleep(0.5)
    confirm_btn = driver.find_element(By.ID, "btnConfirmDelete")
    confirm_btn.click()

    # Wait for success message
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
    )

    # Verify device is gone via API
    verify_response = requests.get(
        f"{API_BASE_URL}/device/00:11:22:33:44:55",
        headers=headers
    )
    assert verify_response.status_code == 404, "Device should be deleted"
```

## Resources

- [Selenium Python Docs](https://selenium-python.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [WebDriver Wait Conditions](https://selenium-python.readthedocs.io/waits.html)
