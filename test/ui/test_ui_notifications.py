#!/usr/bin/env python3
"""
Notifications Page UI Tests
Tests notification table, mark as read, delete operations
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

from test_helpers import BASE_URL, api_get


@pytest.mark.ui
def test_notifications_page_loads(driver):
    """Test: Notifications page loads successfully"""
    driver.get(f"{BASE_URL}/userNotifications.php")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    assert "notification" in driver.page_source.lower(), "Page should contain notification content"


@pytest.mark.ui
def test_notifications_table_present(driver):
    """Test: Notifications table is rendered"""
    driver.get(f"{BASE_URL}/userNotifications.php")
    time.sleep(2)
    table = driver.find_elements(By.CSS_SELECTOR, "table, #notificationsTable")
    assert len(table) > 0, "Notifications table should be present"


@pytest.mark.ui
def test_notification_action_buttons_present(driver):
    """Test: Notification action buttons are visible"""
    driver.get(f"{BASE_URL}/userNotifications.php")
    time.sleep(2)
    buttons = driver.find_elements(By.CSS_SELECTOR, "button[id*='notification'], .notification-action")
    assert len(buttons) > 0, "Notification action buttons should be present"


@pytest.mark.ui
def test_unread_notifications_api(api_token):
    """Test: Unread notifications API endpoint works"""
    response = api_get("/messaging/in-app/unread", api_token)
    assert response.status_code == 200, "API should return 200"

    data = response.json()
    assert isinstance(data, (list, dict)), "API should return list or dict"
