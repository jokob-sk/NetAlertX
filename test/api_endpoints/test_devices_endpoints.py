# import pathlib
# import sqlite3
import base64
import random
# import string
# import uuid
import pytest

from helper import get_setting_value
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
    return "aa:bb:cc:" + ":".join(f"{random.randint(0, 255):02X}" for _ in range(3)).lower()


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
    client.post(f"/device/{test_mac}", json=payload, headers=auth_headers(api_token))


def delete_dummy(client, api_token, test_mac):
    client.delete("/devices", json={"macs": [test_mac]}, headers=auth_headers(api_token))


def test_get_all_devices(client, api_token, test_mac):
    # Ensure there is at least one device
    create_dummy(client, api_token, test_mac)

    # Fetch all devices
    resp = client.get("/devices", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
    devices = resp.json.get("devices")
    assert isinstance(devices, list)
    # Ensure our test device is in the list
    assert any(d["devMac"] == test_mac for d in devices)


def test_delete_devices_with_macs(client, api_token, test_mac):
    # First create device so it exists
    create_dummy(client, api_token, test_mac)

    client.post(f"/device/{test_mac}", json={"createNew": True}, headers=auth_headers(api_token))

    # Delete by MAC
    resp = client.delete("/devices", json={"macs": [test_mac]}, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


def test_delete_all_empty_macs(client, api_token):
    resp = client.delete("/devices/empty-macs", headers=auth_headers(api_token))
    assert resp.status_code == 200
    # Expect success flag in response
    assert resp.json.get("success") is True


def test_delete_unknown_devices(client, api_token):
    resp = client.delete("/devices/unknown", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True


def test_export_devices_csv(client, api_token, test_mac):
    # Create a device first
    create_dummy(client, api_token, test_mac)

    # Export devices as CSV
    resp = client.get("/devices/export/csv", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "attachment; filename=devices.csv" in resp.headers.get("Content-disposition", "")

    # CSV should contain test_mac
    assert test_mac in resp.data.decode()


def test_export_devices_json(client, api_token, test_mac):
    # Create a device first
    create_dummy(client, api_token, test_mac)

    # Export devices as JSON
    resp = client.get("/devices/export/json", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert any(dev.get("devMac") == test_mac for dev in data["data"])


def test_export_devices_invalid_format(client, api_token):
    # Request with unsupported format
    resp = client.get("/devices/export/invalid", headers=auth_headers(api_token))
    assert resp.status_code == 400
    assert "Unsupported format" in resp.json.get("error")


def test_export_import_cycle_base64(client, api_token, test_mac):
    # 1. Create a dummy device
    create_dummy(client, api_token, test_mac)

    # 2. Export devices as CSV
    resp = client.get("/devices/export/csv", headers=auth_headers(api_token))
    assert resp.status_code == 200
    csv_data = resp.data.decode("utf-8")

    print(csv_data)

    # Ensure our dummy device is in the CSV
    assert test_mac in csv_data
    assert "Test Device" in csv_data

    # 3. Base64-encode the CSV for JSON payload
    csv_base64 = base64.b64encode(csv_data.encode("utf-8")).decode("utf-8")
    json_payload = {"content": csv_base64}

    # 4. POST to import endpoint with JSON content
    resp = client.post(
        "/devices/import",
        json=json_payload,
        headers={**auth_headers(api_token), "Content-Type": "application/json"}
    )
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # 5. Verify import results
    assert resp.json.get("inserted") >= 1
    assert resp.json.get("skipped_lines") == []


def test_devices_totals(client, api_token, test_mac):
    create_dummy(client, api_token, test_mac)
    try:
        # 1. Call the totals endpoint
        resp = client.get("/devices/totals", headers=auth_headers(api_token))
        assert resp.status_code == 200

        # 2. Ensure the response is a JSON list
        data = resp.json
        assert isinstance(data, list)

        # 3. Verify the response has exactly 6 elements in documented order:
        # [all, connected, favorites, new, down, archived]
        expected_length = 6
        assert len(data) == expected_length, (
            f"Expected 6 totals (all, connected, favorites, new, down, archived), got {len(data)}"
        )

        # 4. Check that at least 1 device exists (all count includes the dummy device)
        assert data[0] >= 1  # index 0 = 'all'
    finally:
        delete_dummy(client, api_token, test_mac)


def test_devices_by_status(client, api_token, test_mac):
    create_dummy(client, api_token, test_mac)
    try:
        # 1. Request devices by a valid status
        resp = client.get("/devices/by-status?status=my", headers=auth_headers(api_token))
        assert resp.status_code == 200
        data = resp.json
        assert isinstance(data, list)
        assert any(d["id"] == test_mac for d in data)

        # 2. Request devices with an invalid/unknown status
        resp_invalid = client.get("/devices/by-status?status=invalid_status", headers=auth_headers(api_token))
        # Strict validation now returns 422 for invalid status enum values
        assert resp_invalid.status_code == 422

        # 3. Check favorite formatting if devFavorite = 1
        # Update dummy device to favorite
        update_resp = client.post(
            f"/device/{test_mac}",
            json={"devFavorite": 1},
            headers=auth_headers(api_token)
        )
        assert update_resp.status_code == 200
        assert update_resp.json.get("success") is True

        resp_fav = client.get("/devices/by-status?status=my", headers=auth_headers(api_token))
        fav_data = next((d for d in resp_fav.json if d["id"] == test_mac), None)
        assert fav_data is not None
        assert "&#9733" in fav_data["title"]
    finally:
        delete_dummy(client, api_token, test_mac)


def test_devices_by_status_pagination(client, api_token):
    """limit/offset must page through the same set ORDER BY devMac gives
    unpaginated, with no gaps or duplicates, and must reject invalid values.
    Doesn't assume an otherwise-empty DB: reconstructs the full 'my' list from
    pages and compares it to the unpaginated response instead of asserting
    exact positions for the 3 dummies.
    """
    macs = [f"aa:bb:cc:dd:ee:0{i}" for i in (1, 2, 3)]
    for mac in macs:
        create_dummy(client, api_token, mac)

    try:
        full_resp = client.get("/devices/by-status?status=my", headers=auth_headers(api_token))
        assert full_resp.status_code == 200
        full_macs = [d["id"] for d in full_resp.json]
        assert set(macs).issubset(set(full_macs))

        # Page through the full set in halves and confirm the reassembled
        # list matches the unpaginated one exactly (no gaps/duplicates).
        total = len(full_macs)
        half = (total + 1) // 2
        page1 = client.get(
            f"/devices/by-status?status=my&limit={half}&offset=0",
            headers=auth_headers(api_token),
        ).json
        page2 = client.get(
            f"/devices/by-status?status=my&limit={total - half}&offset={half}",
            headers=auth_headers(api_token),
        ).json
        paged_macs = [d["id"] for d in page1] + [d["id"] for d in page2]
        assert paged_macs == full_macs

        # offset alone (no limit) must still take effect, not be silently
        # dropped - regression guard for the LIMIT -1 OFFSET ? fallback.
        offset_only = client.get(
            f"/devices/by-status?status=my&offset={half}",
            headers=auth_headers(api_token),
        ).json
        assert [d["id"] for d in offset_only] == full_macs[half:]

        # Invalid limit/offset are rejected, not silently clamped.
        resp_bad_limit = client.get(
            "/devices/by-status?status=my&limit=0", headers=auth_headers(api_token)
        )
        assert resp_bad_limit.status_code == 422

        resp_bad_offset = client.get(
            "/devices/by-status?status=my&offset=-1", headers=auth_headers(api_token)
        )
        assert resp_bad_offset.status_code == 422
    finally:
        for mac in macs:
            delete_dummy(client, api_token, mac)


def test_get_all_devices_pagination(client, api_token):
    """limit/offset on GET /devices must page through the same set the
    unpaginated response gives, ordered by devMac, with no gaps or
    duplicates, and must reject invalid values."""
    macs = [f"aa:bb:cc:dd:ff:0{i}" for i in (1, 2, 3)]
    for mac in macs:
        create_dummy(client, api_token, mac)

    try:
        full_resp = client.get("/devices", headers=auth_headers(api_token))
        assert full_resp.status_code == 200
        full_macs = [d["devMac"] for d in full_resp.json["devices"]]
        assert set(macs).issubset(set(full_macs))

        total = len(full_macs)
        half = (total + 1) // 2
        page1 = client.get(
            f"/devices?limit={half}&offset=0", headers=auth_headers(api_token)
        ).json["devices"]
        page2 = client.get(
            f"/devices?limit={total - half}&offset={half}",
            headers=auth_headers(api_token),
        ).json["devices"]
        paged_macs = [d["devMac"] for d in page1] + [d["devMac"] for d in page2]
        assert paged_macs == full_macs

        # offset alone (no limit) must still take effect.
        offset_only = client.get(
            f"/devices?offset={half}", headers=auth_headers(api_token)
        ).json["devices"]
        assert [d["devMac"] for d in offset_only] == full_macs[half:]

        # Invalid limit/offset are rejected, not silently clamped.
        resp_bad_limit = client.get(
            "/devices?limit=0", headers=auth_headers(api_token)
        )
        assert resp_bad_limit.status_code == 422

        resp_bad_offset = client.get(
            "/devices?offset=-1", headers=auth_headers(api_token)
        )
        assert resp_bad_offset.status_code == 422
    finally:
        for mac in macs:
            delete_dummy(client, api_token, mac)


def test_delete_test_devices(client, api_token):

    # Delete by MAC
    resp = client.delete("/devices", json={"macs": ["aa:bb:cc:*"]}, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True
