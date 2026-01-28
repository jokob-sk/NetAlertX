"""
Unit tests for device IP update logic (devPrimaryIPv4/devPrimaryIPv6 handling).
"""

from unittest.mock import Mock, patch

import pytest

from server.scan import device_handling


@pytest.fixture
def mock_device_handling():
    """Mock device_handling dependencies."""
    with patch.multiple(
        device_handling,
        update_devPresentLastScan_based_on_nics=Mock(return_value=0),
        update_devPresentLastScan_based_on_force_status=Mock(return_value=0),
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
            scanMac, scanLastIP, scanVendor, scanSourcePlugin, scanName,
            scanLastQuery, scanLastConnection, scanSyncHubNode,
            scanSite, scanSSID, scanParentMAC, scanParentPort, scanType
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
    device_handling.update_ipv4_ipv6(db)

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
            scanMac, scanLastIP, scanVendor, scanSourcePlugin, scanName,
            scanLastQuery, scanLastConnection, scanSyncHubNode,
            scanSite, scanSSID, scanParentMAC, scanParentPort, scanType
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
    device_handling.update_ipv4_ipv6(db)

    row = cur.execute(
        "SELECT devLastIP, devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("11:22:33:44:55:66",),
    ).fetchone()

    assert row["devLastIP"] == "10.0.0.5"
    assert row["devPrimaryIPv4"] == "10.0.0.5"
    assert row["devPrimaryIPv6"] == "2001:db8::2"
