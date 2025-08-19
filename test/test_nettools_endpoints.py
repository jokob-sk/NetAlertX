import sys
import pathlib
import sqlite3
import base64
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


def create_dummy(client, api_token, test_mac):
    payload = {
        "createNew": True,
        "devName": "Test Device",
        "devOwner": "Unit Test",
        "devType": "Router",
        "devVendor": "TestVendor",
    }
    resp = client.post(f"/device/{test_mac}", json=payload, headers=auth_headers(api_token))

def test_wakeonlan_device(client, api_token, test_mac):
    # 1. Ensure at least one device exists
    create_dummy(client, api_token, test_mac)

    # 2. Fetch all devices
    resp = client.get("/devices", headers=auth_headers(api_token))
    assert resp.status_code == 200
    devices = resp.json.get("devices", [])
    assert len(devices) > 0

    # 3. Pick the first device (or the test device)
    device_mac = devices[0]["devMac"]

    # 4. Call the wakeonlan endpoint
    resp = client.post(
        "/nettools/wakeonlan",
        json={"devMac": device_mac},
        headers=auth_headers(api_token)
    )

    # 5. Conditional assertions based on MAC
    if device_mac.lower() == 'internet' or device_mac == test_mac:
        # For athe dummy "internet" or test MAC, expect a 400 response
        assert resp.status_code == 400
    else:
        # For any other MAC, expect a 200 response
        assert resp.status_code == 200
        data = resp.json
        assert data.get("success") is True
        assert "WOL packet sent" in data.get("message", "")

def test_speedtest_endpoint(client, api_token):
    # 1. Call the speedtest endpoint
    resp = client.get("/nettools/speedtest", headers=auth_headers(api_token))

    # 2. Assertions
    if resp.status_code == 403:
        # Unauthorized access
        data = resp.json
        assert "error" in data
        assert data["error"] == "Forbidden"
    else:
        # Expect success
        assert resp.status_code == 200
        data = resp.json
        assert data.get("success") is True
        assert "output" in data
        assert isinstance(data["output"], list)
        # Optionally check that output lines are strings
        assert all(isinstance(line, str) for line in data["output"])
        
def test_traceroute_device(client, api_token, test_mac):
    # 1. Ensure at least one device exists
    create_dummy(client, api_token, test_mac)

    # 2. Fetch all devices
    resp = client.get("/devices", headers=auth_headers(api_token))
    assert resp.status_code == 200
    devices = resp.json.get("devices", [])
    assert len(devices) > 0

    # 3. Pick the first device
    device_ip = devices[0].get("devLastIP", "192.168.1.1")  # fallback if dummy has no IP

    # 4. Call the traceroute endpoint
    resp = client.post(
        "/nettools/traceroute",
        json={"devLastIP": device_ip},
        headers=auth_headers(api_token)
    )

    # 5. Assertions
    if not device_ip or device_ip.lower() == 'invalid':
        # Expect 400 if IP is missing or invalid
        assert resp.status_code == 400
        data = resp.json
        assert data.get("success") is False
    else:
        # Expect 200 and valid traceroute output
        assert resp.status_code == 200
        data = resp.json
        assert data.get("success") is True
        assert "output" in data
        assert isinstance(data["output"], str)


