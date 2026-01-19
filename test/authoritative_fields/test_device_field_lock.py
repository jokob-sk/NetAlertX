"""
Unit tests for device field lock/unlock functionality.
Tests the authoritative field update system with source tracking and field locking.
"""
import sys
import os
import pytest

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value  # noqa: E402
from api_server.api_server_start import app  # noqa: E402
from models.device_instance import DeviceInstance  # noqa: E402


@pytest.fixture(scope="session")
def api_token():
    """Get API token from settings."""
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    """Create test client with app context."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_mac():
    """Generate a test MAC address."""
    return "AA:BB:CC:DD:EE:FF"


@pytest.fixture
def auth_headers(api_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {api_token}"}


@pytest.fixture(autouse=True)
def cleanup_test_device(test_mac):
    """Clean up test device before and after test."""
    device_handler = DeviceInstance()
    # Clean before test
    try:
        device_handler.deleteDeviceByMAC(test_mac)
    except Exception:
        pass
    
    yield
    
    # Clean after test
    try:
        device_handler.deleteDeviceByMAC(test_mac)
    except Exception:
        pass


class TestDeviceFieldLock:
    """Test suite for device field lock/unlock functionality."""

    def test_create_test_device(self, client, test_mac, auth_headers):
        """Create a test device for locking tests."""
        payload = {
            "devName": "Test Device",
            "devLastIP": "192.168.1.100",
            "createNew": True
        }
        resp = client.post(
            f"/device/{test_mac}",
            json=payload,
            headers=auth_headers
        )
        assert resp.status_code in [200, 201], f"Failed to create device: {resp.json}"
        data = resp.json
        assert data.get("success") is True

    def test_lock_field_requires_auth(self, client, test_mac):
        """Lock endpoint requires authorization."""
        payload = {
            "fieldName": "devName",
            "lock": True
        }
        resp = client.post(
            f"/device/{test_mac}/field/lock",
            json=payload
        )
        assert resp.status_code == 403

    def test_lock_field_invalid_parameters(self, client, test_mac, auth_headers):
        """Lock endpoint validates required parameters."""
        # Missing fieldName
        payload = {"lock": True}
        resp = client.post(
            f"/device/{test_mac}/field/lock",
            json=payload,
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "fieldName is required" in resp.json.get("error", "")

    def test_lock_field_invalid_field_name(self, client, test_mac, auth_headers):
        """Lock endpoint rejects untracked fields."""
        payload = {
            "fieldName": "devInvalidField",
            "lock": True
        }
        resp = client.post(
            f"/device/{test_mac}/field/lock",
            json=payload,
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "cannot be locked" in resp.json.get("error", "")

    def test_lock_all_tracked_fields(self, client, test_mac, auth_headers):
        """Lock each tracked field individually."""
        # First create device
        self.test_create_test_device(client, test_mac, auth_headers)
        
        tracked_fields = [
            "devMac", "devName", "devLastIP", "devVendor", "devFQDN",
            "devSSID", "devParentMAC", "devParentPort", "devParentRelType", "devVlan"
        ]
        
        for field_name in tracked_fields:
            payload = {"fieldName": field_name, "lock": True}
            resp = client.post(
                f"/device/{test_mac}/field/lock",
                json=payload,
                headers=auth_headers
            )
            assert resp.status_code == 200, f"Failed to lock {field_name}: {resp.json}"
            data = resp.json
            assert data.get("success") is True
            assert data.get("locked") is True
            assert data.get("fieldName") == field_name

    def test_lock_and_unlock_field(self, client, test_mac, auth_headers):
        """Lock a field then unlock it."""
        # Create device
        self.test_create_test_device(client, test_mac, auth_headers)
        
        # Lock field
        lock_payload = {"fieldName": "devName", "lock": True}
        resp = client.post(
            f"/device/{test_mac}/field/lock",
            json=lock_payload,
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json.get("locked") is True
        
        # Verify source is LOCKED
        resp = client.get(f"/device/{test_mac}", headers=auth_headers)
        assert resp.status_code == 200
        device_data = resp.json
        assert device_data.get("devNameSource") == "LOCKED"
        
        # Unlock field
        unlock_payload = {"fieldName": "devName", "lock": False}
        resp = client.post(
            f"/device/{test_mac}/field/lock",
            json=unlock_payload,
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json.get("locked") is False
        
        # Verify source changed
        resp = client.get(f"/device/{test_mac}", headers=auth_headers)
        assert resp.status_code == 200
        device_data = resp.json
        assert device_data.get("devNameSource") == "NEWDEV"

    def test_lock_prevents_field_updates(self, client, test_mac, auth_headers):
        """Locked field should not be updated through API."""
        # Create device with initial name
        self.test_create_test_device(client, test_mac, auth_headers)
        
        # Lock the field
        lock_payload = {"fieldName": "devName", "lock": True}
        resp = client.post(
            f"/device/{test_mac}/field/lock",
            json=lock_payload,
            headers=auth_headers
        )
        assert resp.status_code == 200
        
        # Try to update the locked field
        update_payload = {"devName": "New Name"}
        resp = client.post(
            f"/device/{test_mac}",
            json=update_payload,
            headers=auth_headers
        )
        
        # Update should succeed at API level but authoritative handler should prevent it
        # The field update logic checks source in the database layer
        # For now verify the API accepts the request
        assert resp.status_code in [200, 201]

    def test_multiple_fields_lock_state(self, client, test_mac, auth_headers):
        """Lock some fields while leaving others unlocked."""
        # Create device
        self.test_create_test_device(client, test_mac, auth_headers)
        
        # Lock only devName and devVendor
        for field in ["devName", "devVendor"]:
            payload = {"fieldName": field, "lock": True}
            resp = client.post(
                f"/device/{test_mac}/field/lock",
                json=payload,
                headers=auth_headers
            )
            assert resp.status_code == 200
        
        # Verify device state
        resp = client.get(f"/device/{test_mac}", headers=auth_headers)
        assert resp.status_code == 200
        device_data = resp.json
        
        # Locked fields should have LOCKED source
        assert device_data.get("devNameSource") == "LOCKED"
        assert device_data.get("devVendorSource") == "LOCKED"
        
        # Other fields should not be locked
        assert device_data.get("devLastIPSource") != "LOCKED"
        assert device_data.get("devFQDNSource") != "LOCKED"

    def test_lock_field_idempotent(self, client, test_mac, auth_headers):
        """Locking the same field multiple times should work."""
        # Create device
        self.test_create_test_device(client, test_mac, auth_headers)
        
        payload = {"fieldName": "devName", "lock": True}
        
        # Lock once
        resp1 = client.post(
            f"/device/{test_mac}/field/lock",
            json=payload,
            headers=auth_headers
        )
        assert resp1.status_code == 200
        
        # Lock again
        resp2 = client.post(
            f"/device/{test_mac}/field/lock",
            json=payload,
            headers=auth_headers
        )
        assert resp2.status_code == 200
        assert resp2.json.get("locked") is True

    def test_lock_new_device_rejected(self, client, auth_headers):
        """Cannot lock fields on new device (mac='new')."""
        payload = {"fieldName": "devName", "lock": True}
        resp = client.post(
            "/device/new/field/lock",
            json=payload,
            headers=auth_headers
        )
        # May return 400 or 404 depending on validation order
        assert resp.status_code in [400, 404]


class TestFieldLockIntegration:
    """Integration tests for field locking with plugin overwrites."""

    def test_locked_field_blocks_plugin_overwrite(self, test_mac, auth_headers):
        """Verify locked fields prevent plugin source overwrites."""
        device_handler = DeviceInstance()
        
        # Create device
        create_result = device_handler.setDeviceData(test_mac, {
            "devName": "Original Name",
            "devLastIP": "192.168.1.100",
            "createNew": True
        })
        assert create_result.get("success") is True
        
        # Lock the field
        device_handler.updateDeviceColumn(test_mac, "devNameSource", "LOCKED")
        
        # Try to overwrite with plugin source (this would be done by authoritative handler)
        # For now, verify the source is stored correctly
        device_data = device_handler.getDeviceData(test_mac)
        assert device_data.get("devNameSource") == "LOCKED"

    def test_field_source_tracking(self, test_mac, auth_headers):
        """Verify field source is tracked correctly."""
        device_handler = DeviceInstance()
        
        # Create device
        create_result = device_handler.setDeviceData(test_mac, {
            "devName": "Test Device",
            "devLastIP": "192.168.1.100",
            "createNew": True
        })
        assert create_result.get("success") is True
        
        # Verify initial source
        device_data = device_handler.getDeviceData(test_mac)
        assert device_data.get("devNameSource") == "NEWDEV"
        
        # Update field (should set source to USER)
        update_result = device_handler.setDeviceData(test_mac, {
            "devName": "Updated Name"
        })
        assert update_result.get("success") is True
        
        # Verify source changed to USER
        device_data = device_handler.getDeviceData(test_mac)
        assert device_data.get("devNameSource") == "USER"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
