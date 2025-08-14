import sys
import pathlib
import sqlite3
import random
import string
import uuid
import pytest

INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import timeNowTZ, get_setting_value
from api_server.api_server_start import app

@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_mac():
    # Generate a unique MAC for each test run
    return "AA:BB:CC:" + ":".join(f"{random.randint(0,255):02X}" for _ in range(3))

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_create_device(client, api_token, test_mac):
    payload = {
        "createNew": True,
        "name": "Test Device",
        "owner": "Unit Test",
        "type": "Router",
        "vendor": "TestVendor",
    }
    resp = client.post(f"/device/{test_mac}", json=payload, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

def test_get_device(client, api_token, test_mac):
    # First create it
    client.post(f"/device/{test_mac}", json={"createNew": True}, headers=auth_headers(api_token))
    # Then retrieve it
    resp = client.get(f"/device/{test_mac}", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("devMac") == test_mac

def test_reset_device_props(client, api_token, test_mac):
    client.post(f"/device/{test_mac}", json={"createNew": True}, headers=auth_headers(api_token))
    resp = client.post(f"/device/{test_mac}/reset-props", json={}, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

def test_delete_device_events(client, api_token, test_mac):
    client.post(f"/device/{test_mac}", json={"createNew": True}, headers=auth_headers(api_token))
    resp = client.delete(f"/device/{test_mac}/events/delete", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

def test_delete_device(client, api_token, test_mac):
    client.post(f"/device/{test_mac}", json={"createNew": True}, headers=auth_headers(api_token))
    resp = client.delete(f"/device/{test_mac}/delete", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
