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

def create_event(client, api_token, mac, event="UnitTest Event", days_old=None):
    """
    Create event using API (POST /event/<mac>).
    If days_old is set, adds it to payload for backdating support.
    """
    payload = {
        "event": event,
    }
    if days_old:
        payload["days_old"] = days_old
    return client.post(f"/event/{mac}", json=payload, headers=auth_headers(api_token))

def list_events(client, api_token, mac=None):
    url = "/events" if mac is None else f"/events/{mac}"
    return client.get(url, headers=auth_headers(api_token))


def test_delete_events_for_mac(client, api_token, test_mac):
    # create event
    resp = create_event(client, api_token, test_mac)
    assert resp.status_code == 200

    # confirm exists
    resp = list_events(client, api_token, test_mac)
    assert resp.status_code == 200
    assert any(ev["eve_MAC"] == test_mac for ev in resp.json)

    # delete
    resp = client.delete(f"/events/{test_mac}", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # confirm deleted
    resp = list_events(client, api_token, test_mac)
    assert resp.status_code == 200
    assert len(resp.json) == 0


def test_delete_all_events(client, api_token, test_mac):
    # create two events
    create_event(client, api_token, test_mac)
    create_event(client, api_token, "FF:FF:FF:FF:FF:FF")

    resp = list_events(client, api_token)
    assert len(resp.json) >= 2

    # delete all
    resp = client.delete("/events", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # confirm no events
    resp = list_events(client, api_token)
    assert len(resp.json) == 0


def test_delete_events_30days(client, api_token, test_mac):
    # create old + new events
    create_event(client, api_token, test_mac, days_old=40)  # should be deleted
    create_event(client, api_token, test_mac, days_old=5)   # should remain

    resp = list_events(client, api_token, test_mac)
    assert len(resp.json) == 2

    # delete events older than 30 days
    resp = client.delete("/events/30days", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # confirm only recent remains
    resp = list_events(client, api_token, test_mac)
    mac_events = [ev for ev in resp.json if ev["eve_MAC"] == test_mac]
    assert len(mac_events) == 1
