import sys
import os
import pytest
from unittest.mock import patch, MagicMock

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value  # noqa: E402
from api_server.api_server_start import app  # noqa: E402


@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# --- get_device_info Tests ---
@patch('api_server.tools_routes.get_temp_db_connection')
def test_get_device_info_ip_partial(mock_db_conn, client, api_token):
    """Test get_device_info with partial IP search."""
    mock_cursor = MagicMock()
    # Mock return of a device with IP ending in .50
    mock_cursor.fetchall.return_value = [
        {"devName": "Test Device", "devMac": "AA:BB:CC:DD:EE:FF", "devLastIP": "192.168.1.50"}
    ]
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    payload = {"query": ".50"}
    response = client.post('/api/tools/get_device_info',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    devices = response.get_json()
    assert len(devices) == 1
    assert devices[0]["devLastIP"] == "192.168.1.50"

    # Verify SQL query included 3 params (MAC, Name, IP)
    args, _ = mock_cursor.execute.call_args
    assert args[0].count("?") == 3
    assert len(args[1]) == 3


# --- trigger_scan Tests ---
@patch('subprocess.run')
def test_trigger_scan_nmap_fast(mock_run, client, api_token):
    """Test trigger_scan with nmap_fast."""
    mock_run.return_value = MagicMock(stdout="Scan completed", returncode=0)

    payload = {"scan_type": "nmap_fast", "target": "192.168.1.1"}
    response = client.post('/api/tools/trigger_scan',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "nmap -F 192.168.1.1" in data["command"]
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_trigger_scan_invalid_type(mock_run, client, api_token):
    """Test trigger_scan with invalid scan_type."""
    payload = {"scan_type": "invalid_type", "target": "192.168.1.1"}
    response = client.post('/api/tools/trigger_scan',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 400
    mock_run.assert_not_called()

# --- get_open_ports Tests ---


@patch('subprocess.run')
def test_get_open_ports_ip(mock_run, client, api_token):
    """Test get_open_ports with an IP address."""
    mock_output = """
Starting Nmap 7.80 ( https://nmap.org ) at 2023-10-27 10:00 UTC
Nmap scan report for 192.168.1.1
Host is up (0.0010s latency).
Not shown: 98 closed ports
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
Nmap done: 1 IP address (1 host up) scanned in 0.10 seconds
"""
    mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)

    payload = {"target": "192.168.1.1"}
    response = client.post('/api/tools/get_open_ports',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["open_ports"]) == 2
    assert data["open_ports"][0]["port"] == 22
    assert data["open_ports"][1]["service"] == "http"


@patch('api_server.tools_routes.get_temp_db_connection')
@patch('subprocess.run')
def test_get_open_ports_mac_resolve(mock_run, mock_db_conn, client, api_token):
    """Test get_open_ports with a MAC address that resolves to an IP."""
    # Mock DB to resolve MAC to IP
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"devLastIP": "192.168.1.50"}
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    # Mock Nmap output
    mock_run.return_value = MagicMock(stdout="80/tcp open http", returncode=0)

    payload = {"target": "AA:BB:CC:DD:EE:FF"}
    response = client.post('/api/tools/get_open_ports',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["target"] == "192.168.1.50"  # Should be resolved IP
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert "192.168.1.50" in args[0]


# --- get_network_topology Tests ---
@patch('api_server.tools_routes.get_temp_db_connection')
def test_get_network_topology(mock_db_conn, client, api_token):
    """Test get_network_topology."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {"devName": "Router", "devMac": "AA:AA:AA:AA:AA:AA", "devParentMAC": None, "devParentPort": None, "devVendor": "VendorA"},
        {"devName": "Device1", "devMac": "BB:BB:BB:BB:BB:BB", "devParentMAC": "AA:AA:AA:AA:AA:AA", "devParentPort": "eth1", "devVendor": "VendorB"}
    ]
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    response = client.get('/api/tools/get_network_topology',
                          headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert len(data["nodes"]) == 2
    assert len(data["links"]) == 1
    assert data["links"][0]["source"] == "AA:AA:AA:AA:AA:AA"
    assert data["links"][0]["target"] == "BB:BB:BB:BB:BB:BB"


# --- get_recent_alerts Tests ---
@patch('api_server.tools_routes.get_temp_db_connection')
def test_get_recent_alerts(mock_db_conn, client, api_token):
    """Test get_recent_alerts."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {"eve_DateTime": "2023-10-27 10:00:00", "eve_EventType": "New Device", "eve_MAC": "CC:CC:CC:CC:CC:CC", "eve_IP": "192.168.1.100", "devName": "Unknown"}
    ]
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    payload = {"hours": 24}
    response = client.post('/api/tools/get_recent_alerts',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["eve_EventType"] == "New Device"


# --- set_device_alias Tests ---
@patch('api_server.tools_routes.get_temp_db_connection')
def test_set_device_alias(mock_db_conn, client, api_token):
    """Test set_device_alias."""
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1  # Simulate successful update
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    payload = {"mac": "AA:BB:CC:DD:EE:FF", "alias": "New Name"}
    response = client.post('/api/tools/set_device_alias',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


@patch('api_server.tools_routes.get_temp_db_connection')
def test_set_device_alias_not_found(mock_db_conn, client, api_token):
    """Test set_device_alias when device is not found."""
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0  # Simulate no rows updated
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    payload = {"mac": "AA:BB:CC:DD:EE:FF", "alias": "New Name"}
    response = client.post('/api/tools/set_device_alias',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 404


# --- wol_wake_device Tests ---
@patch('subprocess.run')
def test_wol_wake_device(mock_subprocess, client, api_token):
    """Test wol_wake_device."""
    mock_subprocess.return_value.stdout = "Sending magic packet to 255.255.255.255:9 with AA:BB:CC:DD:EE:FF"
    mock_subprocess.return_value.returncode = 0

    payload = {"mac": "AA:BB:CC:DD:EE:FF"}
    response = client.post('/api/tools/wol_wake_device',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    mock_subprocess.assert_called_with(["wakeonlan", "AA:BB:CC:DD:EE:FF"], capture_output=True, text=True, check=True)


@patch('api_server.tools_routes.get_temp_db_connection')
@patch('subprocess.run')
def test_wol_wake_device_by_ip(mock_subprocess, mock_db_conn, client, api_token):
    """Test wol_wake_device with IP address."""
    # Mock DB for IP resolution
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"devMac": "AA:BB:CC:DD:EE:FF"}
    mock_db_conn.return_value.cursor.return_value = mock_cursor

    # Mock subprocess
    mock_subprocess.return_value.stdout = "Sending magic packet to 255.255.255.255:9 with AA:BB:CC:DD:EE:FF"
    mock_subprocess.return_value.returncode = 0

    payload = {"ip": "192.168.1.50"}
    response = client.post('/api/tools/wol_wake_device',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "AA:BB:CC:DD:EE:FF" in data["message"]

    # Verify DB lookup
    mock_cursor.execute.assert_called_with("SELECT devMac FROM Devices WHERE devLastIP = ?", ("192.168.1.50",))

    # Verify subprocess call
    mock_subprocess.assert_called_with(["wakeonlan", "AA:BB:CC:DD:EE:FF"], capture_output=True, text=True, check=True)


def test_wol_wake_device_invalid_mac(client, api_token):
    """Test wol_wake_device with invalid MAC."""
    payload = {"mac": "invalid-mac"}
    response = client.post('/api/tools/wol_wake_device',
                           json=payload,
                           headers=auth_headers(api_token))

    assert response.status_code == 400


# --- openapi_spec Tests ---
def test_openapi_spec(client):
    """Test openapi_spec endpoint contains new paths."""
    response = client.get('/api/tools/openapi.json')
    assert response.status_code == 200
    spec = response.get_json()

    # Check for new endpoints
    assert "/trigger_scan" in spec["paths"]
    assert "/get_open_ports" in spec["paths"]
    assert "/get_network_topology" in spec["paths"]
    assert "/get_recent_alerts" in spec["paths"]
    assert "/set_device_alias" in spec["paths"]
    assert "/wol_wake_device" in spec["paths"]
