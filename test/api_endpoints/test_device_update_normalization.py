
import pytest
import random
from helper import get_setting_value
from api_server.api_server_start import app
from models.device_instance import DeviceInstance

@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_mac_norm():
    # Normalized MAC
    return "AA:BB:CC:DD:EE:FF"

@pytest.fixture
def test_parent_mac_input():
    # Lowercase input MAC
    return "aa:bb:cc:dd:ee:00"

@pytest.fixture
def test_parent_mac_norm():
    # Normalized expected MAC
    return "AA:BB:CC:DD:EE:00"

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_update_normalization(client, api_token, test_mac_norm, test_parent_mac_input, test_parent_mac_norm):
    # 1. Create a device (using normalized MAC)
    create_payload = {
        "createNew": True,
        "devName": "Normalization Test Device",
        "devOwner": "Unit Test",
    }
    resp = client.post(f"/device/{test_mac_norm}", json=create_payload, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # 2. Update the device using LOWERCASE MAC in URL
    # And set devParentMAC to LOWERCASE
    update_payload = {
        "devParentMAC": test_parent_mac_input,
        "devName": "Updated Device"
    }
    # Using lowercase MAC in URL: aa:bb:cc:dd:ee:ff
    lowercase_mac = test_mac_norm.lower()
    
    resp = client.post(f"/device/{lowercase_mac}", json=update_payload, headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

    # 3. Verify in DB that devParentMAC is NORMALIZED
    device_handler = DeviceInstance()
    device = device_handler.getDeviceData(test_mac_norm)
    
    assert device is not None
    assert device["devName"] == "Updated Device"
    # This is the critical check:
    assert device["devParentMAC"] == test_parent_mac_norm
    assert device["devParentMAC"] != test_parent_mac_input # Should verify it changed from input if input was different case

    # Cleanup
    device_handler.deleteDeviceByMAC(test_mac_norm)
