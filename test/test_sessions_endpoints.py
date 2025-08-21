import sys
import pathlib
import sqlite3
import random
import string
import uuid
import pytest
from datetime import datetime, timedelta

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
        "devType": "Test Device",
        "devOwner": "Unit Test",
        "devType": "Router",
        "devVendor": "TestVendor",
    }
    resp = client.post(f"/device/{test_mac}", json=payload, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


# -----------------------------
# CREATE SESSION
# -----------------------------
def test_create_session(client, api_token, test_mac):
    payload = {
        "mac": test_mac,
        "ip": "192.168.1.100",
        "start_time": timeNowTZ(),
        "event_type_conn": "Connected",
        "event_type_disc": "Disconnected"
    }
    resp = client.post("/sessions/create", json=payload, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


# -----------------------------
# LIST SESSIONS
# -----------------------------
def test_list_sessions(client, api_token, test_mac):
    # Ensure at least one session exists
    payload = {
        "mac": test_mac,
        "ip": "192.168.1.100",
        "start_time": timeNowTZ()
    }
    client.post("/sessions/create", json=payload, headers=auth_headers(api_token))

    # List sessions for MAC
    resp = client.get(f"/sessions/list?mac={test_mac}", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
    sessions = resp.json.get("sessions")
    assert any(ses["ses_MAC"] == test_mac for ses in sessions)


# -----------------------------
# DELETE SESSION
# -----------------------------
def test_delete_session(client, api_token, test_mac):
    # First create session
    payload = {
        "mac": test_mac,
        "ip": "192.168.1.100",
        "start_time": timeNowTZ()
    }
    client.post("/sessions/create", json=payload, headers=auth_headers(api_token))

    # Delete session
    resp = client.delete("/sessions/delete", json={"mac": test_mac}, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # Confirm deletion
    resp = client.get(f"/sessions/list?mac={test_mac}", headers=auth_headers(api_token))
    sessions = resp.json.get("sessions")
    assert not any(ev["ses_MAC"] == test_mac for ses in sessions)



def test_get_sessions_calendar(client, api_token, test_mac):
    """
    Test the /sessions/calendar endpoint.
    Creates session and ensures the calendar output is correct.
    Cleans up test sessions after test.
    """
    

    # --- Setup: create two sessions for the test MAC ---
    now = timeNowTZ()
    start1 = (now - timedelta(days=2)).isoformat(timespec="seconds")
    end1   = (now - timedelta(days=1, hours=20)).isoformat(timespec="seconds")

    start2 = (now - timedelta(days=1)).isoformat(timespec="seconds")
    end2   = (now - timedelta(hours=20)).isoformat(timespec="seconds")

    # Create sessions using your endpoint
    client.post("/sessions/create", json={
        "mac": test_mac,
        "ip": "192.168.1.100",
        "start_time": start1,
        "end_time": end1,
        "event_type_conn": "connect",
        "event_type_disc": "disconnect"
    }, headers=auth_headers(api_token))

    client.post("/sessions/create", json={
        "mac": test_mac,
        "ip": "192.168.1.100",
        "start_time": start2,
        "end_time": end2,
        "event_type_conn": "connect",
        "event_type_disc": "disconnect"
    }, headers=auth_headers(api_token))

    # --- Call the /sessions/calendar API ---
    start_date = (now - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date   = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    resp = client.get(
        f"/sessions/calendar?start={start_date}&end={end_date}",
        headers=auth_headers(api_token)
    )

    assert resp.status_code == 200
    data = resp.json
    assert data.get("success") is True
    assert "sessions" in data
    sessions = data["sessions"]

    # --- Verify calendar sessions ---
    assert len(sessions) >= 2  # at least our two sessions

    # Check expected keys
    expected_keys = {"resourceId", "title", "start", "end", "color", "tooltip", "className"}
    for ses in sessions:
        assert set(ses.keys()) == expected_keys

    # Check that all sessions belong to the test MAC
    mac_sessions = [ses for ses in sessions if ses["resourceId"] == test_mac]
    assert len(mac_sessions) == 2  # or exact number if you know it

    # Check ISO date formatting for start/end
    for ses in mac_sessions:
        # start must always be present
        assert ses["start"] is not None, f"Session start is None: {ses}"
        datetime.fromisoformat(ses["start"])

        # end can be None only if tooltip mentions "<still connected>"
        if ses["end"] is not None:
            datetime.fromisoformat(ses["end"])
        else:
            assert "<still connected>" in ses["tooltip"], f"End is None but session not marked as still connected: {ses}"

    # --- Cleanup: delete all test sessions for this MAC ---
    client.delete(f"/sessions/delete?mac={test_mac}", headers=auth_headers(api_token))