"""
Integration tests for device field locking during actual scan updates.

Simulates real-world scenarios by:
1. Setting up Devices table with various source values
2. Populating CurrentScan with new discovery data
3. Running actual device_handling scan updates
4. Verifying field updates respect authorization rules

Tests all combinations of field sources (LOCKED, USER, NEWDEV, plugin name)
with realistic scan data.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

from server.scan import device_handling

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    DummyDB,
    insert_current_scan_row_from_dict,
    insert_device_from_dict,
    make_current_scan_dict,
    make_device_dict,
)


@pytest.fixture
def mock_device_handlers():
    """Mock device_handling helper functions."""
    with patch.multiple(
        device_handling,
        update_devPresentLastScan_based_on_nics=Mock(return_value=0),
        update_devPresentLastScan_based_on_force_status=Mock(return_value=0),
        query_MAC_vendor=Mock(return_value=-1),
        guess_icon=Mock(return_value="icon"),
        guess_type=Mock(return_value="type"),
        get_setting_value=Mock(
            side_effect=lambda key: {
                "NEWDEV_replace_preset_icon": 0,
                "NEWDEV_devIcon": "icon",
                "NEWDEV_devType": "type",
            }.get(key, "")
        ),
    ):
        yield


def test_create_new_devices_sets_sources(scan_db):
    """New device insert initializes source fields from scan method."""
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:10",
            scanName="DeviceOne",
            scanVendor="AcmeVendor",
            scanSourcePlugin="ARPSCAN",
            scanLastIP="192.168.1.10",
            scanParentMAC="11:22:33:44:55:66",
            scanParentPort="1",
            scanSSID="MyWifi",
        ),
    )

    settings = {
        "NEWDEV_devType": "default-type",
        "NEWDEV_devParentMAC": "ff:ff:ff:ff:ff:ff",
        "NEWDEV_devOwner": "owner",
        "NEWDEV_devGroup": "group",
        "NEWDEV_devComments": "",
        "NEWDEV_devLocation": "",
        "NEWDEV_devCustomProps": "",
        "NEWDEV_devParentRelType": "uplink",
        "SYNC_node_name": "SYNCNODE",
    }

    db = DummyDB(scan_db)

    with patch.multiple(
        device_handling,
        get_setting_value=Mock(side_effect=lambda key: settings.get(key, "")),
        safe_int=Mock(return_value=0),
    ):
        device_handling.create_new_devices(db)

    row = scan_db.execute(
        """
        SELECT
            devMacSource,
            devNameSource,
            devVendorSource,
            devLastIPSource,
            devSSIDSource,
            devParentMACSource,
            devParentPortSource,
            devParentRelTypeSource,
            devFQDNSource,
            devVlanSource
        FROM Devices WHERE devMac = ?
        """,
        ("aa:bb:cc:dd:ee:10",),
    ).fetchone()

    assert row["devMacSource"] == "ARPSCAN"
    assert row["devNameSource"] == "ARPSCAN"
    assert row["devVendorSource"] == "ARPSCAN"
    assert row["devLastIPSource"] == "ARPSCAN"
    assert row["devSSIDSource"] == "ARPSCAN"
    assert row["devParentMACSource"] == "ARPSCAN"
    assert row["devParentPortSource"] == "ARPSCAN"
    assert row["devParentRelTypeSource"] == "NEWDEV"
    assert row["devFQDNSource"] == "NEWDEV"
    assert row["devVlanSource"] == "NEWDEV"


def test_create_new_devices_ignores_dangling_newdev_parentmac(scan_db):
    """A stale NEWDEV_devParentMAC pointing to a since-deleted device is treated as unset,
    instead of seeding the new device with another dangling Parent Node reference."""
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:11",
            scanName="DeviceTwo",
            scanVendor="AcmeVendor",
            scanSourcePlugin="ARPSCAN",
            scanLastIP="192.168.1.11",
        ),
    )

    settings = {
        "NEWDEV_devType": "default-type",
        # points to a MAC that does not (and never did, in this test) exist in Devices
        "NEWDEV_devParentMAC": "99:99:99:99:99:99",
        "NEWDEV_devOwner": "owner",
        "NEWDEV_devGroup": "group",
        "NEWDEV_devComments": "",
        "NEWDEV_devLocation": "",
        "NEWDEV_devCustomProps": "",
        "NEWDEV_devParentRelType": "uplink",
        "SYNC_node_name": "SYNCNODE",
    }

    db = DummyDB(scan_db)

    with patch.multiple(
        device_handling,
        get_setting_value=Mock(side_effect=lambda key: settings.get(key, "")),
        safe_int=Mock(return_value=0),
    ):
        device_handling.create_new_devices(db)

    row = scan_db.execute(
        "SELECT devParentMAC FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:11",)
    ).fetchone()

    assert row["devParentMAC"] == ""


def test_scan_updates_newdev_device_name(scan_db, mock_device_handlers):
    """Scanner discovers name for device with NEWDEV source."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:01",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=0,
            devLastIP="192.168.1.1",
            devName="",  # No name yet
            devNameSource="NEWDEV",
            devVendor="TestVendor",
            devVendorSource="NEWDEV",
            devLastIPSource="ARPSCAN",
        ),
    )

    # Scanner discovers name
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:01",
            scanLastIP="192.168.1.1",
            scanVendor="TestVendor",
            scanSourcePlugin="NBTSCAN",
            scanName="DiscoveredDevice",
            scanLastQuery="",
            scanLastConnection="2025-01-01 01:00:00",
        ),
    )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)

    row = scan_db.execute(
        "SELECT devName FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:01",),
    ).fetchone()

    # Name SHOULD be updated from NEWDEV
    assert row["devName"] == "DiscoveredDevice", "Name should be updated from empty"


def test_scan_does_not_update_user_field_name(scan_db, mock_device_handlers):
    """Scanner cannot override devName when source is USER."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:02",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=0,
            devLastIP="192.168.1.2",
            devName="My Custom Device",
            devNameSource="USER",  # User-owned
            devVendor="TestVendor",
            devVendorSource="NEWDEV",
            devLastIPSource="ARPSCAN",
        ),
    )

    # Scanner tries to update name
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:02",
            scanLastIP="192.168.1.2",
            scanVendor="TestVendor",
            scanSourcePlugin="NBTSCAN",
            scanName="ScannedDevice",
            scanLastQuery="",
            scanLastConnection="2025-01-01 01:00:00",
        ),
    )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)

    row = scan_db.execute(
        "SELECT devName FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:02",),
    ).fetchone()

    # Name should NOT be updated because it's USER-owned
    assert row["devName"] == "My Custom Device", "USER name should not be changed by scan"


def test_scan_does_not_update_locked_field(scan_db, mock_device_handlers):
    """Scanner cannot override LOCKED devName."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:03",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=0,
            devLastIP="192.168.1.3",
            devName="Important Device",
            devNameSource="LOCKED",  # Locked
            devVendor="TestVendor",
            devVendorSource="NEWDEV",
            devLastIPSource="ARPSCAN",
        ),
    )

    # Scanner tries to update name
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:03",
            scanLastIP="192.168.1.3",
            scanVendor="TestVendor",
            scanSourcePlugin="NBTSCAN",
            scanName="Unknown",
            scanLastQuery="",
            scanLastConnection="2025-01-01 01:00:00",
        ),
    )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)

    row = scan_db.execute(
        "SELECT devName FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:03",),
    ).fetchone()

    # Name should NOT be updated because it's LOCKED
    assert row["devName"] == "Important Device", "LOCKED name should not be changed"


def test_scan_updates_empty_vendor_field(scan_db, mock_device_handlers):
    """Scan updates vendor when it's empty/NULL."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:04",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=0,
            devLastIP="192.168.1.4",
            devName="Device",
            devNameSource="NEWDEV",
            devVendor="",  # Empty vendor
            devVendorSource="NEWDEV",
            devLastIPSource="ARPSCAN",
        ),
    )

    # Scan discovers vendor
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:04",
            scanLastIP="192.168.1.4",
            scanVendor="Apple Inc.",
            scanSourcePlugin="ARPSCAN",
            scanName="",
            scanLastQuery="",
            scanLastConnection="2025-01-01 01:00:00",
        ),
    )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)

    row = scan_db.execute(
        "SELECT devVendor FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:04",),
    ).fetchone()

    # Vendor SHOULD be updated
    assert row["devVendor"] == "Apple Inc.", "Empty vendor should be populated from scan"


def test_scan_updates_ip_addresses(scan_db, mock_device_handlers):
    """Scan updates IPv4 and IPv6 addresses correctly."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:05",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=0,
            devLastIP="",
            devName="Device",
            devNameSource="NEWDEV",
            devVendor="Vendor",
            devVendorSource="NEWDEV",
            devLastIPSource="NEWDEV",
            devPrimaryIPv4="",  # No IPv4
            devPrimaryIPv6="",  # No IPv6
        ),
    )

    # Scan discovers IPv4
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:05",
            scanLastIP="192.168.1.100",
            scanVendor="Vendor",
            scanSourcePlugin="ARPSCAN",
            scanName="",
            scanLastQuery="",
            scanLastConnection="2025-01-01 01:00:00",
        ),
    )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)
    device_handling.update_ipv4_ipv6(db)

    row = scan_db.execute(
        "SELECT devLastIP, devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:05",),
    ).fetchone()

    # IPv4 should be set
    assert row["devLastIP"] == "192.168.1.100", "Last IP should be updated"
    assert row["devPrimaryIPv4"] == "192.168.1.100", "Primary IPv4 should be set"
    assert row["devPrimaryIPv6"] == "", "IPv6 should remain empty"


def test_scan_updates_ipv6_without_changing_ipv4(scan_db, mock_device_handlers):
    """Scan updates IPv6 without overwriting IPv4."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:06",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=0,
            devLastIP="192.168.1.101",
            devName="Device",
            devNameSource="NEWDEV",
            devVendor="Vendor",
            devVendorSource="NEWDEV",
            devLastIPSource="NEWDEV",
            devPrimaryIPv4="192.168.1.101",  # IPv4 already set
            devPrimaryIPv6="",  # No IPv6
        ),
    )

    # Scan discovers IPv6
    insert_current_scan_row_from_dict(
        scan_db,
        make_current_scan_dict(
            "aa:bb:cc:dd:ee:06",
            scanLastIP="fe80::1",
            scanVendor="Vendor",
            scanSourcePlugin="ARPSCAN",
            scanName="",
            scanLastQuery="",
            scanLastConnection="2025-01-01 01:00:00",
        ),
    )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)
    device_handling.update_ipv4_ipv6(db)

    row = scan_db.execute(
        "SELECT devPrimaryIPv4, devPrimaryIPv6 FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:06",),
    ).fetchone()

    # IPv4 should remain, IPv6 should be set
    assert row["devPrimaryIPv4"] == "192.168.1.101", "IPv4 should not change"
    assert row["devPrimaryIPv6"] == "fe80::1", "IPv6 should be set"


def test_scan_updates_presence_status(scan_db, mock_device_handlers):
    """Scan correctly updates devPresentLastScan status."""
    insert_device_from_dict(
        scan_db,
        make_device_dict(
            "aa:bb:cc:dd:ee:07",
            devLastConnection="2025-01-01 00:00:00",
            devPresentLastScan=1,  # Was online
            devLastIP="192.168.1.102",
            devName="Device",
            devNameSource="NEWDEV",
            devVendor="Vendor",
            devVendorSource="NEWDEV",
            devLastIPSource="ARPSCAN",
        ),
    )

    # Note: No CurrentScan entry for this MAC - device is offline

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)
    device_handling.update_presence_from_CurrentScan(db)

    row = scan_db.execute(
        "SELECT devPresentLastScan FROM Devices WHERE devMac = ?",
        ("aa:bb:cc:dd:ee:07",),
    ).fetchone()

    # Device should be marked as offline
    assert row["devPresentLastScan"] == 0, "Offline device should have devPresentLastScan = 0"


def test_scan_multiple_devices_mixed_sources(scan_db, mock_device_handlers):
    """Scan with multiple devices having different source combinations."""
    devices_data = [
        # (MAC, Name, NameSource, Vendor, VendorSource)
        ("aa:bb:cc:dd:ee:11", "Device1", "NEWDEV", "", "NEWDEV"),  # Both updatable
        ("aa:bb:cc:dd:ee:12", "My Device", "USER", "OldVendor", "NEWDEV"),  # Name protected
        ("aa:bb:cc:dd:ee:13", "Locked Device", "LOCKED", "", "NEWDEV"),  # Name locked
        ("aa:bb:cc:dd:ee:14", "Device4", "ARPSCAN", "", "NEWDEV"),  # Name from plugin
    ]

    for mac, name, name_src, vendor, vendor_src in devices_data:
        insert_device_from_dict(
            scan_db,
            make_device_dict(
                mac,
                devLastConnection="2025-01-01 00:00:00",
                devPresentLastScan=0,
                devLastIP="192.168.1.1",
                devName=name,
                devNameSource=name_src,
                devVendor=vendor,
                devVendorSource=vendor_src,
                devLastIPSource="ARPSCAN",
            ),
        )

    # Scan discovers all devices with new data
    scan_entries = [
        ("aa:bb:cc:dd:ee:11", "192.168.1.1", "Apple Inc.", "ScanPlugin", "ScannedDevice1"),
        ("aa:bb:cc:dd:ee:12", "192.168.1.2", "Samsung", "ScanPlugin", "ScannedDevice2"),
        ("aa:bb:cc:dd:ee:13", "192.168.1.3", "Sony", "ScanPlugin", "ScannedDevice3"),
        ("aa:bb:cc:dd:ee:14", "192.168.1.4", "LG", "ScanPlugin", "ScannedDevice4"),
    ]

    for mac, ip, vendor, scan_method, name in scan_entries:
        insert_current_scan_row_from_dict(
            scan_db,
            make_current_scan_dict(
                mac,
                scanLastIP=ip,
                scanVendor=vendor,
                scanSourcePlugin=scan_method,
                scanName=name,
                scanLastQuery="",
                scanLastConnection="2025-01-01 01:00:00",
            ),
        )

    db = Mock()
    db.sql_connection = scan_db
    db.sql = scan_db.cursor()

    # Run scan update
    device_handling.update_devices_data_from_scan(db)

    # Check results
    results = {
        "aa:bb:cc:dd:ee:11": {"name": "Device1", "vendor": "Apple Inc."},  # Name already set, won't update
        "aa:bb:cc:dd:ee:12": {"name": "My Device", "vendor": "Samsung"},  # Name protected (USER)
        "aa:bb:cc:dd:ee:13": {"name": "Locked Device", "vendor": "Sony"},  # Name locked
        "aa:bb:cc:dd:ee:14": {"name": "Device4", "vendor": "LG"},  # Name already from plugin, won't update
    }

    for mac, expected in results.items():
        row = scan_db.execute(
            "SELECT devName, devVendor FROM Devices WHERE devMac = ?",
            (mac,),
        ).fetchone()
        assert row["devName"] == expected["name"], f"Device {mac} name mismatch: got {row['devName']}, expected {expected['name']}"
