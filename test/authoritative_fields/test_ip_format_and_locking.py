"""
Tests for IP format validation and field locking interactions.

Covers:
- IPv4/IPv6 format validation
- Invalid IP rejection
- IP field locking scenarios
- IP source tracking
"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from server.scan import device_handling


@pytest.fixture
def ip_test_db():
    """Create an in-memory SQLite database for IP format testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE Devices (
            devMac TEXT PRIMARY KEY,
            devLastConnection TEXT,
            devPresentLastScan INTEGER,
            devForceStatus TEXT,
            devLastIP TEXT,
            devLastIpSource TEXT DEFAULT 'NEWDEV',
            devPrimaryIPv4 TEXT,
            devPrimaryIPv4Source TEXT DEFAULT 'NEWDEV',
            devPrimaryIPv6 TEXT,
            devPrimaryIPv6Source TEXT DEFAULT 'NEWDEV',
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
def mock_ip_handlers():
    """Mock device_handling helper functions."""
    with patch.multiple(
        device_handling,
        update_devPresentLastScan_based_on_nics=Mock(return_value=0),
        update_devPresentLastScan_based_on_force_status=Mock(return_value=0),
        query_MAC_vendor=Mock(return_value=-1),
        guess_icon=Mock(return_value="icon"),
        guess_type=Mock(return_value="type"),
        get_setting_value=Mock(return_value=""),
    ):
        yield


def test_valid_ipv4_format_accepted(ip_test_db, mock_ip_handlers):
    """Valid IPv4 address should be accepted and set as primary IPv4."""
    cur = ip_test_db.cursor()

    # Device with no IPs
    cur.execute(
        """
        INSERT INTO Devices (
            devMac, devLastConnection, devPresentLastScan, devLastIP,
            devPrimaryIPv4, devPrimaryIPv6, devVendor, devType, devIcon,
            devName, devParentPort, devParentMAC, devSite, devSSID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:01",
            "2025-01-01 00:00:00",
            0,
            "",
            "",
            "",
            "Vendor",
            "type",
            "icon",
            "Device",
            "",
            "",
            "",
            "",
        ),
    )

    # Scan discovers valid IPv4
    cur.execute(
        """
        INSERT INTO CurrentScan (
            cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
            cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
            cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:01",
            "192.168.1.100",
            "Vendor",
            "ARPSCAN",
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
    ip_test_db.commit()

    db = Mock()
    db.sql_connection = ip_test_db
    db.sql = cur

    device_handling.update_devices_data_from_scan(db)

    row = cur.execute(
        "SELECT devLastIP, devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("AA:BB:CC:DD:EE:01",),
    ).fetchone()

    assert row["devLastIP"] == "192.168.1.100", "Valid IPv4 should update devLastIP"
    assert row["devPrimaryIPv4"] == "192.168.1.100", "Valid IPv4 should set devPrimaryIPv4"
    assert row["devPrimaryIPv6"] == "", "IPv6 should remain empty"


def test_valid_ipv6_format_accepted(ip_test_db, mock_ip_handlers):
    """Valid IPv6 address should be accepted and set as primary IPv6."""
    cur = ip_test_db.cursor()

    # Device with no IPs
    cur.execute(
        """
        INSERT INTO Devices (
            devMac, devLastConnection, devPresentLastScan, devLastIP,
            devPrimaryIPv4, devPrimaryIPv6, devVendor, devType, devIcon,
            devName, devParentPort, devParentMAC, devSite, devSSID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:02",
            "2025-01-01 00:00:00",
            0,
            "",
            "",
            "",
            "Vendor",
            "type",
            "icon",
            "Device",
            "",
            "",
            "",
            "",
        ),
    )

    # Scan discovers valid IPv6
    cur.execute(
        """
        INSERT INTO CurrentScan (
            cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
            cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
            cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:02",
            "fe80::1",
            "Vendor",
            "ARPSCAN",
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
    ip_test_db.commit()

    db = Mock()
    db.sql_connection = ip_test_db
    db.sql = cur

    device_handling.update_devices_data_from_scan(db)

    row = cur.execute(
        "SELECT devLastIP, devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("AA:BB:CC:DD:EE:02",),
    ).fetchone()

    assert row["devLastIP"] == "fe80::1", "Valid IPv6 should update devLastIP"
    assert row["devPrimaryIPv4"] == "", "IPv4 should remain empty"
    assert row["devPrimaryIPv6"] == "fe80::1", "Valid IPv6 should set devPrimaryIPv6"


def test_invalid_ip_values_rejected(ip_test_db, mock_ip_handlers):
    """Invalid IP values like (unknown), null, empty should be rejected."""
    cur = ip_test_db.cursor()

    # Device with existing valid IPv4
    cur.execute(
        """
        INSERT INTO Devices (
            devMac, devLastConnection, devPresentLastScan, devLastIP,
            devPrimaryIPv4, devPrimaryIPv6, devVendor, devType, devIcon,
            devName, devParentPort, devParentMAC, devSite, devSSID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:03",
            "2025-01-01 00:00:00",
            0,
            "192.168.1.50",
            "192.168.1.50",
            "",
            "Vendor",
            "type",
            "icon",
            "Device",
            "",
            "",
            "",
            "",
        ),
    )

    invalid_ips = ["", "null", "(unknown)", "(Unknown)"]

    for invalid_ip in invalid_ips:
        cur.execute("DELETE FROM CurrentScan")
        cur.execute(
            """
            INSERT INTO CurrentScan (
                cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
                cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
                cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "AA:BB:CC:DD:EE:03",
                invalid_ip,
                "Vendor",
                "ARPSCAN",
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
        ip_test_db.commit()

        db = Mock()
        db.sql_connection = ip_test_db
        db.sql = cur

        device_handling.update_devices_data_from_scan(db)

        row = cur.execute(
            "SELECT devPrimaryIPv4 FROM Devices WHERE devMac = ?",
            ("AA:BB:CC:DD:EE:03",),
        ).fetchone()

        assert (
            row["devPrimaryIPv4"] == "192.168.1.50"
        ), f"Invalid IP '{invalid_ip}' should not overwrite valid IPv4"


def test_ipv4_ipv6_mixed_in_multiple_scans(ip_test_db, mock_ip_handlers):
    """Multiple scans with different IP types should set both primary fields correctly."""
    cur = ip_test_db.cursor()

    # Device with no IPs
    cur.execute(
        """
        INSERT INTO Devices (
            devMac, devLastConnection, devPresentLastScan, devLastIP,
            devPrimaryIPv4, devPrimaryIPv6, devVendor, devType, devIcon,
            devName, devParentPort, devParentMAC, devSite, devSSID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:04",
            "2025-01-01 00:00:00",
            0,
            "",
            "",
            "",
            "Vendor",
            "type",
            "icon",
            "Device",
            "",
            "",
            "",
            "",
        ),
    )

    # Scan 1: IPv4
    cur.execute(
        """
        INSERT INTO CurrentScan (
            cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
            cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
            cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:04",
            "192.168.1.100",
            "Vendor",
            "ARPSCAN",
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
    ip_test_db.commit()

    db = Mock()
    db.sql_connection = ip_test_db
    db.sql = cur

    device_handling.update_devices_data_from_scan(db)

    row1 = cur.execute(
        "SELECT devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("AA:BB:CC:DD:EE:04",),
    ).fetchone()

    assert row1["devPrimaryIPv4"] == "192.168.1.100"
    assert row1["devPrimaryIPv6"] == ""

    # Scan 2: IPv6 (should add IPv6 without changing IPv4)
    cur.execute("DELETE FROM CurrentScan")
    cur.execute(
        """
        INSERT INTO CurrentScan (
            cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
            cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
            cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "AA:BB:CC:DD:EE:04",
            "fe80::1",
            "Vendor",
            "ARPSCAN",
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
    ip_test_db.commit()

    db.sql = cur
    device_handling.update_devices_data_from_scan(db)

    row2 = cur.execute(
        "SELECT devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("AA:BB:CC:DD:EE:04",),
    ).fetchone()

    assert row2["devPrimaryIPv4"] == "192.168.1.100", "IPv4 should be preserved"
    assert row2["devPrimaryIPv6"] == "fe80::1", "IPv6 should be set"


def test_ipv4_address_format_variations(ip_test_db, mock_ip_handlers):
    """Test various valid IPv4 formats."""
    cur = ip_test_db.cursor()

    ipv4_addresses = [
        "0.0.0.0",
        "127.0.0.1",
        "192.168.1.1",
        "10.0.0.1",
        "172.16.0.1",
        "255.255.255.255",
    ]

    for idx, ipv4 in enumerate(ipv4_addresses):
        mac = f"AA:BB:CC:DD:EE:{idx:02X}"

        cur.execute(
            """
            INSERT INTO Devices (
                devMac, devLastConnection, devPresentLastScan, devLastIP,
                devPrimaryIPv4, devPrimaryIPv6, devVendor, devType, devIcon,
                devName, devParentPort, devParentMAC, devSite, devSSID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mac, "2025-01-01 00:00:00", 0, "", "", "", "Vendor", "type", "icon", "Device", "", "", "", ""),
        )

        cur.execute(
            """
            INSERT INTO CurrentScan (
                cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
                cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
                cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mac, ipv4, "Vendor", "ARPSCAN", "", "", "2025-01-01 01:00:00", "", "", "", "", "", ""),
        )

    ip_test_db.commit()

    db = Mock()
    db.sql_connection = ip_test_db
    db.sql = cur

    device_handling.update_devices_data_from_scan(db)

    for idx, expected_ipv4 in enumerate(ipv4_addresses):
        mac = f"AA:BB:CC:DD:EE:{idx:02X}"
        row = cur.execute(
            "SELECT devPrimaryIPv4 FROM Devices WHERE devMac = ?",
            (mac,),
        ).fetchone()
        assert row["devPrimaryIPv4"] == expected_ipv4, f"IPv4 {expected_ipv4} should be set for {mac}"


def test_ipv6_address_format_variations(ip_test_db, mock_ip_handlers):
    """Test various valid IPv6 formats."""
    cur = ip_test_db.cursor()

    ipv6_addresses = [
        "::1",
        "fe80::1",
        "2001:db8::1",
        "::ffff:192.0.2.1",
        "2001:0db8:85a3::8a2e:0370:7334",
    ]

    for idx, ipv6 in enumerate(ipv6_addresses):
        mac = f"BB:BB:CC:DD:EE:{idx:02X}"

        cur.execute(
            """
            INSERT INTO Devices (
                devMac, devLastConnection, devPresentLastScan, devLastIP,
                devPrimaryIPv4, devPrimaryIPv6, devVendor, devType, devIcon,
                devName, devParentPort, devParentMAC, devSite, devSSID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mac, "2025-01-01 00:00:00", 0, "", "", "", "Vendor", "type", "icon", "Device", "", "", "", ""),
        )

        cur.execute(
            """
            INSERT INTO CurrentScan (
                cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod, cur_Name,
                cur_LastQuery, cur_DateTime, cur_SyncHubNodeName,
                cur_NetworkSite, cur_SSID, cur_NetworkNodeMAC, cur_PORT, cur_Type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mac, ipv6, "Vendor", "ARPSCAN", "", "", "2025-01-01 01:00:00", "", "", "", "", "", ""),
        )

    ip_test_db.commit()

    db = Mock()
    db.sql_connection = ip_test_db
    db.sql = cur

    device_handling.update_devices_data_from_scan(db)

    for idx, expected_ipv6 in enumerate(ipv6_addresses):
        mac = f"BB:BB:CC:DD:EE:{idx:02X}"
        row = cur.execute(
            "SELECT devPrimaryIPv6 FROM Devices WHERE devMac = ?",
            (mac,),
        ).fetchone()
        assert row["devPrimaryIPv6"] == expected_ipv6, f"IPv6 {expected_ipv6} should be set for {mac}"
