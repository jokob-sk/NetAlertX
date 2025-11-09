import sys
import pathlib
import sqlite3
import random
import string
import uuid
import os
import pytest
from datetime import datetime, timedelta

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value
from utils.datetime_utils import timeNowTZ
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
    payload = {"ip": "0.0.0.0", "event_type": event}

    # Calculate the event_time if days_old is given
    if days_old is not None:
        event_time = timeNowTZ() - timedelta(days=days_old)
        # ISO 8601 string
        payload["event_time"] = event_time.isoformat()

    return client.post(f"/events/create/{mac}", json=payload, headers=auth_headers(api_token))

def list_events(client, api_token, mac=None):
    url = "/events" if mac is None else f"/events?mac={mac}"
    return client.get(url, headers=auth_headers(api_token))

def test_create_event(client, api_token, test_mac):
    # create event
    resp = create_event(client, api_token, test_mac)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True

    # confirm event exists
    resp = list_events(client, api_token, test_mac)
    assert resp.status_code == 200
    events = resp.get_json().get("events", [])
    assert any(ev.get("eve_MAC") == test_mac for ev in events)


def test_delete_events_for_mac(client, api_token, test_mac):
    # create event
    resp = create_event(client, api_token, test_mac)
    assert resp.status_code == 200

    # confirm exists
    resp = list_events(client, api_token, test_mac)
    assert resp.status_code == 200
    events = resp.json.get("events", [])
    assert any(ev["eve_MAC"] == test_mac for ev in events)

    # delete
    resp = client.delete(f"/events/{test_mac}", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # confirm deleted
    resp = list_events(client, api_token, test_mac)
    assert resp.status_code == 200
    assert len(resp.json.get("events", [])) == 0

def test_get_events_totals(client, api_token):
    # 1. Request totals with default period
    resp = client.get(
        "/sessions/totals",
        headers=auth_headers(api_token)
    )
    assert resp.status_code == 200

    data = resp.json
    assert isinstance(data, list)
    # Expecting 6 counts: all_events, sessions, missing, voided, new, down
    assert len(data) == 6
    for count in data:
        assert isinstance(count, int)  # each should be a number

    # 2. Request totals with custom period
    resp_month = client.get(
        "/sessions/totals?period=1 month",
        headers=auth_headers(api_token)
    )
    assert resp_month.status_code == 200
    data_month = resp_month.json
    assert isinstance(data_month, list)
    assert len(data_month) == 6



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
    assert len(resp.json.get("events", [])) == 0


def test_delete_events_dynamic_days(client, api_token, test_mac):
    # create old + new events
    create_event(client, api_token, test_mac, days_old=40)  # should be deleted
    create_event(client, api_token, test_mac, days_old=5)   # should remain

    resp = list_events(client, api_token, test_mac)
    assert len(resp.json) == 2

    # delete events older than 30 days
    resp = client.delete("/events/30", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
    assert "Deleted events older than 30 days" in resp.json.get("message", "")

    # confirm only recent remains
    resp = list_events(client, api_token, test_mac)
    events = resp.get_json().get("events", [])
    mac_events = [ev for ev in events if ev.get("eve_MAC") == test_mac]
    assert len(mac_events) == 1


