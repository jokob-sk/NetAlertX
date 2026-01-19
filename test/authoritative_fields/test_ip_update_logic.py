"""
Unit tests for device IP update logic (devPrimaryIPv4/devPrimaryIPv6 handling).
"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from server.scan import device_handling


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE Devices (
            devMac TEXT PRIMARY KEY,
            devLastConnection TEXT,
            devPresentLastScan INTEGER,
            devLastIP TEXT,
            devPrimaryIPv4 TEXT,
            devPrimaryIPv6 TEXT,
            devVendor TEXT,
            devParentPort TEXT,
            devParentMAC TEXT,
            devSite TEXT,
            devSSID TEXT,
            devType TEXT,
            devName TEXT,
            devIcon TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE CurrentScan (
            cur_MAC TEXT,
            cur_IP TEXT,
            cur_Vendor TEXT,
            cur_ScanMethod TEXT,
            cur_Name TEXT,
            cur_LastQuery TEXT,
            cur_DateTime TEXT,
            cur_SyncHubNodeName TEXT,
            cur_NetworkSite TEXT,
            cur_SSID TEXT,
            cur_NetworkNodeMAC TEXT,
            cur_PORT TEXT,
            cur_Type TEXT
        )
        """
    )

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_device_handling():
    """Mock device_handling dependencies."""
    with patch.multiple(
        device_handling,
        update_devPresentLastScan_based_on_nics=Mock(return_value=0),
        query_MAC_vendor=Mock(return_value=-1),
        guess_icon=Mock(return_value="icon"),
        guess_type=Mock(return_value="type"),
        get_setting_value=Mock(side_effect=lambda key: {
            "NEWDEV_replace_preset_icon": 0,
            "NEWDEV_devIcon": "icon",
            "NEWDEV_devType": "type",
        }.get(key, "")),
    ):
        yield


def test_primary_ipv6_is_set_and_ipv4_preserved(in_memory_db, mock_device_handling):
    """Setting IPv6 in CurrentScan should update devPrimaryIPv6 without changing devPrimaryIPv4."""
    cur = in_memory_db.cursor()

    # Create device with IPv4 primary
    cur.execute(
        """
        INSERT INTO Devices (
            devMac, devLastConnection, devPresentLastScan, devLastIP,
            devPrimaryIPv4, devPrimaryIPv6, devVendor, devParentPort,
            devParentMAC, devSite, devSSID, devType, devName, devIcon
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:FF",
            "2025-01-01 00:00:00",
            0,
            "192.168.1.10",
            "192.168.1.10",
            "",
            "TestVendor",
            "",
            "",
            "",
            "",
            "type",
            "Device",
            "icon",
        ),
    )

    # CurrentScan with IPv6
    cur.execute(
        """
        INSERT INTO CurrentScan (
            cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
            cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
            cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:FF",
            "2001:db8::1",
            "",
            "",
            "",
            "",
            "2025-01-01 01:00:00",
            "",
            "",
            "",
            "",
            "",
            "",
        ),
    )
    in_memory_db.commit()

    # Mock DummyDB-like object
    db = Mock()
    db.sql_connection = in_memory_db
    db.sql = cur
    
    device_handling.update_devices_data_from_scan(db)

    row = cur.execute(
        "SELECT devLastIP, devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("AA:BB:CC:DD:EE:FF",),
    ).fetchone()

    assert row["devLastIP"] == "2001:db8::1"
    assert row["devPrimaryIPv4"] == "192.168.1.10"
    assert row["devPrimaryIPv6"] == "2001:db8::1"


def test_primary_ipv4_is_set_and_ipv6_preserved(in_memory_db, mock_device_handling):
    """Setting IPv4 in CurrentScan should update devPrimaryIPv4 without changing devPrimaryIPv6."""
    cur = in_memory_db.cursor()

    # Create device with IPv6 primary
    cur.execute(
        """
        INSERT INTO Devices (
            devMac, devLastConnection, devPresentLastScan, devLastIP,
            devPrimaryIPv4, devPrimaryIPv6, devVendor, devParentPort,
            devParentMAC, devSite, devSSID, devType, devName, devIcon
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "11:22:33:44:55:66",
            "2025-01-01 00:00:00",
            0,
            "2001:db8::2",
            "",
            "2001:db8::2",
            "TestVendor",
            "",
            "",
            "",
            "",
            "type",
            "Device",
            "icon",
        ),
    )

    # CurrentScan with IPv4
    cur.execute(
        """
        INSERT INTO CurrentScan (
            cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
            cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
            cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "11:22:33:44:55:66",
            "10.0.0.5",
            "",
            "",
            "",
            "",
            "2025-01-01 02:00:00",
            "",
            "",
            "",
            "",
            "",
            "",
        ),
    )
    in_memory_db.commit()

    # Mock DummyDB-like object
    db = Mock()
    db.sql_connection = in_memory_db
    db.sql = cur
    
    device_handling.update_devices_data_from_scan(db)

    row = cur.execute(
        "SELECT devLastIP, devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("11:22:33:44:55:66",),
    ).fetchone()

    assert row["devLastIP"] == "10.0.0.5"
    assert row["devPrimaryIPv4"] == "10.0.0.5"
    assert row["devPrimaryIPv6"] == "2001:db8::2"
