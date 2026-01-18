# -----------------------------
# In-app notifications tests with cleanup
# -----------------------------
import random
import string
import pytest
import os

from api_server.api_server_start import app  # noqa: E402 [flake8 lint suppression]
from messaging.in_app import NOTIFICATION_API_FILE    # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]


@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def random_content():
    return "Test Notification " + "".join(random.choices(string.ascii_letters + string.digits, k=6))


@pytest.fixture
def notification_guid(client, api_token, random_content):
    # Write a notification and return its GUID
    resp = client.post(
        "/messaging/in-app/write",
        json={"content": random_content, "level": "alert"},
        headers=auth_headers(api_token)
    )
    assert resp.status_code == 200
    # Fetch the unread notifications and get GUID
    resp = client.get("/messaging/in-app/unread", headers=auth_headers(api_token))
    data = resp.json
    guid = next((n["guid"] for n in data if n["content"] == random_content), None)
    assert guid is not None
    return guid


@pytest.fixture(autouse=True)
def cleanup_notifications():
    # Runs before and after each test
    # Backup original file if exists
    backup = None
    if os.path.exists(NOTIFICATION_API_FILE):
        with open(NOTIFICATION_API_FILE, "r") as f:
            backup = f.read()

    yield  # run the test

    # Cleanup after test
    with open(NOTIFICATION_API_FILE, "w") as f:
        f.write("[]")

    # Restore backup if needed
    if backup:
        with open(NOTIFICATION_API_FILE, "w") as f:
            f.write(backup)


# -----------------------------
def test_write_notification(client, api_token, random_content):
    resp = client.post(
        "/messaging/in-app/write",
        json={"content": random_content, "level": "alert"},
        headers=auth_headers(api_token)
    )
    assert resp.status_code == 200
    assert resp.json.get("success") is True


def test_get_unread_notifications(client, api_token, random_content):
    client.post("/messaging/in-app/write", json={"content": random_content}, headers=auth_headers(api_token))
    resp = client.get("/messaging/in-app/unread", headers=auth_headers(api_token))
    assert resp.status_code == 200
    notifications = resp.json
    assert any(n["content"] == random_content for n in notifications)


def test_mark_all_notifications_read(client, api_token, random_content):
    client.post("/messaging/in-app/write", json={"content": random_content}, headers=auth_headers(api_token))
    resp = client.post("/messaging/in-app/read/all", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


def test_mark_single_notification_read(client, api_token, notification_guid):
    resp = client.post(f"/messaging/in-app/read/{notification_guid}", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


def test_delete_single_notification(client, api_token, notification_guid):
    resp = client.delete(f"/messaging/in-app/delete/{notification_guid}", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


def test_delete_all_notifications(client, api_token, random_content):
    # Add a notification first
    client.post("/messaging/in-app/write", json={"content": random_content}, headers=auth_headers(api_token))
    resp = client.delete("/messaging/in-app/delete", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
