import sys
import os
import pytest

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from api_server.api_server_start import app  # noqa: E402 [flake8 lint suppression]


@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_openapi_spec(client):
    """Test OpenAPI spec endpoint."""
    response = client.get('/api/tools/openapi.json')
    assert response.status_code == 200
    spec = response.get_json()
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec
    assert "/list_devices" in spec["paths"]
    assert "/get_device_info" in spec["paths"]


def test_list_devices(client, api_token):
    """Test list_devices endpoint."""
    response = client.post('/api/tools/list_devices', headers=auth_headers(api_token))
    assert response.status_code == 200
    devices = response.get_json()
    assert isinstance(devices, list)
    # If there are devices, check structure
    if devices:
        device = devices[0]
        assert "devName" in device
        assert "devMac" in device


def test_get_device_info(client, api_token):
    """Test get_device_info endpoint."""
    # Test with a query that might not exist
    payload = {"query": "nonexistent_device"}
    response = client.post('/api/tools/get_device_info',
                           json=payload,
                           headers=auth_headers(api_token))
    # Should return 404 if no match, or 200 with results
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        devices = response.get_json()
        assert isinstance(devices, list)
    elif response.status_code == 404:
        # Expected for no matches
        pass


def test_list_devices_unauthorized(client):
    """Test list_devices without authorization."""
    response = client.post('/api/tools/list_devices')
    assert response.status_code == 401


def test_get_device_info_unauthorized(client):
    """Test get_device_info without authorization."""
    payload = {"query": "test"}
    response = client.post('/api/tools/get_device_info', json=payload)
    assert response.status_code == 401
