import sys
import os
import pytest
import random
from datetime import timedelta

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from utils.datetime_utils import timeNowUTC  # noqa: E402 [flake8 lint suppression]
from api_server.api_server_start import app  # noqa: E402 [flake8 lint suppression]


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
    return "aa:bb:cc:" + ":".join(f"{random.randint(0, 255):02X}" for _ in range(3)).lower()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_event(client, api_token, mac, event="UnitTest Event", days_old=None):
    payload = {"ip": "0.0.0.0", "event_type": event}

    # Calculate the event_time if days_old is given
    if days_old is not None:
        event_time = timeNowUTC(as_string=False) - timedelta(days=days_old)
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
    assert any(ev.get("eveMac") == test_mac for ev in events)


def test_delete_events_for_mac(client, api_token, test_mac):
    # create event
    resp = create_event(client, api_token, test_mac)
    assert resp.status_code == 200

    # confirm exists
    resp = list_events(client, api_token, test_mac)
    assert resp.status_code == 200
    events = resp.json.get("events", [])
    assert any(ev["eveMac"] == test_mac for ev in events)

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
    create_event(client, api_token, "ff:ff:ff:ff:ff:ff")

    resp = list_events(client, api_token)
    # At least the two we created should be present
    assert len(resp.json.get("events", [])) >= 2

    # delete all
    resp = client.delete("/events", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # confirm no events
    resp = list_events(client, api_token)
    assert len(resp.json.get("events", [])) == 0


def test_get_events_pagination(client, api_token, test_mac):
    """limit/offset on GET /events must page through the same set the
    unpaginated response gives for one MAC, ordered by eveDateTime
    descending, with no gaps or duplicates, and must reject invalid values."""
    # Distinct event_type per call - idx_events_unique is on
    # (eveMac, eveIp, eveEventType, eveDateTime), and eveDateTime only has
    # second precision, so 5 calls in the same second with the same
    # event_type would collide and INSERT OR IGNORE would drop 4 of them.
    for i in range(5):
        create_event(client, api_token, test_mac, event=f"UnitTest Event {i}")

    full_resp = list_events(client, api_token, test_mac)
    assert full_resp.status_code == 200
    full_events = full_resp.json.get("events", [])
    assert len(full_events) >= 5

    total = len(full_events)
    half = (total + 1) // 2
    page1 = client.get(
        f"/events?mac={test_mac}&limit={half}&offset=0",
        headers=auth_headers(api_token),
    ).json.get("events", [])
    page2 = client.get(
        f"/events?mac={test_mac}&limit={total - half}&offset={half}",
        headers=auth_headers(api_token),
    ).json.get("events", [])
    assert page1 + page2 == full_events

    # offset alone (no limit) must still take effect.
    offset_only = client.get(
        f"/events?mac={test_mac}&offset={half}",
        headers=auth_headers(api_token),
    ).json.get("events", [])
    assert offset_only == full_events[half:]

    # Invalid limit/offset are rejected, not silently clamped.
    resp_bad_limit = client.get(
        f"/events?mac={test_mac}&limit=0", headers=auth_headers(api_token)
    )
    assert resp_bad_limit.status_code == 422

    resp_bad_offset = client.get(
        f"/events?mac={test_mac}&offset=-1", headers=auth_headers(api_token)
    )
    assert resp_bad_offset.status_code == 422


def test_get_events_pagination_stable_order_for_ties(client, api_token, test_mac):
    """Events sharing the exact same eveDateTime (a real occurrence - it only
    has second precision) must still page deterministically: ORDER BY
    eveDateTime DESC alone leaves tied rows in an unspecified order, so
    concatenated pages could omit or duplicate rows. rowid DESC as a secondary
    key must make the order stable across the unpaginated and paged calls."""
    # create_event() only sets event_time when days_old is given, so post
    # directly with an explicit, identical event_time for all 5 to force a tie.
    shared_time = timeNowUTC(as_string=False).isoformat()
    for i in range(5):
        payload = {"ip": "0.0.0.0", "event_type": f"TieEventExplicit {i}", "event_time": shared_time}
        resp = client.post(f"/events/create/{test_mac}", json=payload, headers=auth_headers(api_token))
        assert resp.status_code == 200

    full_resp = list_events(client, api_token, test_mac)
    full_events = full_resp.json.get("events", [])
    tied = [e for e in full_events if e.get("eveEventType", "").startswith("TieEventExplicit")]
    assert len(tied) == 5
    assert all(e["eveDateTime"] == tied[0]["eveDateTime"] for e in tied)

    total = len(full_events)
    half = (total + 1) // 2
    page1 = client.get(
        f"/events?mac={test_mac}&limit={half}&offset=0",
        headers=auth_headers(api_token),
    ).json.get("events", [])
    page2 = client.get(
        f"/events?mac={test_mac}&limit={total - half}&offset={half}",
        headers=auth_headers(api_token),
    ).json.get("events", [])
    assert page1 + page2 == full_events


def test_delete_events_dynamic_days(client, api_token, test_mac):
    # Determine initial count so test doesn't rely on preexisting events
    before = list_events(client, api_token, test_mac)
    initial_events = before.json.get("events", [])
    initial_count = len(initial_events)

    # Count pre-existing events younger than 30 days for test_mac
    # These will remain after delete operation
    from datetime import datetime
    thirty_days_ago = timeNowUTC(as_string=False) - timedelta(days=30)
    initial_younger_count = 0
    for ev in initial_events:
        if ev.get("eveMac") == test_mac and ev.get("eveDateTime"):
            try:
                # Parse event datetime (handle ISO format)
                ev_time_str = ev["eveDateTime"]
                # Try parsing with timezone info
                try:
                    ev_time = datetime.fromisoformat(ev_time_str.replace("Z", "+00:00"))
                except ValueError:
                    # Fallback for formats without timezone
                    ev_time = datetime.fromisoformat(ev_time_str)
                if ev_time.tzinfo is None:
                    ev_time = ev_time.replace(tzinfo=thirty_days_ago.tzinfo)
                if ev_time > thirty_days_ago:
                    initial_younger_count += 1
            except (ValueError, TypeError):
                pass  # Skip events with unparseable dates

    # create old + new events
    create_event(client, api_token, test_mac, days_old=40)  # should be deleted
    create_event(client, api_token, test_mac, days_old=5)   # should remain

    resp = list_events(client, api_token, test_mac)
    assert len(resp.json.get("events", [])) == initial_count + 2

    # delete events older than 30 days
    resp = client.delete("/events/30", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
    assert "Deleted events older than 30 days" in resp.json.get("message", "")

    # confirm only recent events remain (pre-existing younger + newly created 5-day-old)
    resp = list_events(client, api_token, test_mac)
    events = resp.get_json().get("events", [])
    mac_events = [ev for ev in events if ev.get("eveMac") == test_mac]
    expected_remaining = initial_younger_count + 1  # 1 for the 5-day-old event we created
    assert len(mac_events) == expected_remaining
