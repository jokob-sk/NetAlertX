"""
Tests for scanCreatesDevice (server/scan/device_handling.py:create_new_devices()).

scanCreatesDevice = 0 lets a plugin report a row without ever originating a
new Devices entry from it (an enrich-only/metadata plugin), while still being
able to update an already-existing device's fields via the separate
update_devices_data_from_scan() code path. Multiple plugins reporting the
same never-before-seen MAC resolve via most-permissive-wins: any row saying 1
creates the device, regardless of how many other rows say 0.
"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_db,
    make_current_scan_dict,
    insert_current_scan_row_from_dict,
    make_device_dict,
    insert_device_from_dict,
    DummyDB,
)

from server.scan import device_handling  # noqa: E402


def _devices(db: DummyDB) -> set:
    rows = db._conn.execute("SELECT devMac FROM Devices").fetchall()
    return {r["devMac"].lower() for r in rows}


class TestScanCreatesDeviceGate:
    def test_scan_creates_device_zero_never_creates(self):
        """A brand-new MAC reported only with scanCreatesDevice=0 is never created."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict("aa:bb:cc:dd:ee:01", scanCreatesDevice=0)
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        assert _devices(db) == set()

    def test_scan_creates_device_one_creates_normally(self):
        """Default (1) preserves today's behavior - regression guard."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict("aa:bb:cc:dd:ee:02", scanCreatesDevice=1)
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        assert _devices(db) == {"aa:bb:cc:dd:ee:02"}

    def test_most_permissive_wins_across_plugins(self):
        """Two plugins report the same never-before-seen MAC: one 0, one 1 -> created."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                "aa:bb:cc:dd:ee:03", scanSourcePlugin="ENRICH", scanCreatesDevice=0
            ),
        )
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                "aa:bb:cc:dd:ee:03", scanSourcePlugin="ARPSCAN", scanCreatesDevice=1
            ),
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        assert _devices(db) == {"aa:bb:cc:dd:ee:03"}

    def test_missing_column_defaults_to_creates(self):
        """An old plugin's row (column never mapped) must default to scanCreatesDevice=1."""
        conn = make_db()
        # Insert without scanCreatesDevice at all - relies on the schema DEFAULT.
        conn.execute(
            "INSERT INTO CurrentScan (scanMac, scanLastIP) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:04", "192.168.1.50"),
        )
        conn.commit()
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        assert _devices(db) == {"aa:bb:cc:dd:ee:04"}


class TestScanCreatesDeviceFieldAuthorityRegression:
    """Locks in that update_devices_data_from_scan() needs zero scanCreatesDevice
    awareness - a scanCreatesDevice=0 row updates an existing device's fields
    exactly like any other row, through the pre-existing FIELD_SPECS/
    can_overwrite_field() authority mechanism."""

    def test_enrich_only_row_still_updates_existing_device(self):
        conn = make_db()
        insert_device_from_dict(
            conn, make_device_dict("aa:bb:cc:dd:ee:05", devName="(unknown)", devNameSource="")
        )
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                "aa:bb:cc:dd:ee:05",
                scanSourcePlugin="NSLOOKUP",
                scanName="resolved-hostname",
                scanCreatesDevice=0,
            ),
        )
        db = DummyDB(conn)

        with patch(
            "server.scan.device_handling.get_plugin_authoritative_settings",
            return_value={},
        ):
            device_handling.update_devices_data_from_scan(db)

        row = conn.execute(
            "SELECT devName FROM Devices WHERE devMac = 'aa:bb:cc:dd:ee:05'"
        ).fetchone()
        assert row["devName"] == "resolved-hostname", (
            "scanCreatesDevice=0 must not block ordinary field updates on an "
            "existing device - identity/creation and field updates are separate paths"
        )


class TestNewDeviceEventNoDuplicatesAcrossPlugins:
    """Multiple plugins reporting the same brand-new MAC with *different*
    scanLastIP/scanVendor values must still produce exactly one 'New Device'
    Events row, not one per distinct (IP, vendor) pair - idx_events_unique
    includes eveIp, so differing IPs are not deduped by the DB itself, and an
    unaggregated SELECT DISTINCT over CurrentScan rows previously produced a
    duplicate row per distinct value combination."""

    def test_differing_ip_and_vendor_collapse_to_one_event(self):
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                "aa:bb:cc:dd:ee:06",
                scanSourcePlugin="ARPSCAN",
                scanLastIP="192.168.1.20",
                scanVendor="Acme",
            ),
        )
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                "aa:bb:cc:dd:ee:06",
                scanSourcePlugin="DOCKER",
                scanLastIP="192.168.1.21",
                scanVendor="Other",
            ),
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType = 'New Device'",
            ("aa:bb:cc:dd:ee:06",),
        ).fetchall()
        assert len(rows) == 1, (
            "differing scanLastIP/scanVendor across plugin rows for the same "
            "new MAC must not produce duplicate New Device events"
        )


class TestBlankMacNeverCreatesDevice:
    """A row with a blank/null-equivalent scanMac must never originate a
    Devices row, even with scanCreatesDevice = 1 (the default) - this is the
    backstop for a plugin that has rows it can't attach a real MAC to but
    forgot to (or can't) set scanCreatesDevice = 0 itself. A well-behaved
    plugin should still set scanCreatesDevice = 0 for such rows (see
    plugin-import-behavior-controls.md) - this guard exists for the case
    where it doesn't, so a blank MAC can never create a device regardless."""

    def test_blank_scanmac_with_creates_device_one_creates_nothing(self):
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict("", scanCreatesDevice=1)
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        assert _devices(db) == set()
        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = '' AND eveEventType = 'New Device'"
        ).fetchall()
        assert rows == [], "a blank scanMac must not produce an orphan New Device event either"

    def test_multiple_plugins_sharing_blank_scanmac_creates_nothing(self):
        """The scenario this guard was actually written for: several
        unrelated rows (e.g. containers with no routable MAC) all reporting
        scanMac = '' collapse into one CurrentScan group - that group must
        never create a device, regardless of how many rows are in it."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict("", scanSourcePlugin="PLUGINA", scanCreatesDevice=0)
        )
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict("", scanSourcePlugin="PLUGINB", scanCreatesDevice=1)
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        assert _devices(db) == set(), (
            "even a single row asserting scanCreatesDevice = 1 for a blank MAC "
            "must not create a device - most-permissive-wins does not override "
            "the blank-MAC guard"
        )
