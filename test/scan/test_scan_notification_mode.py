"""
Tests for scanNotificationMode (server/scan/device_handling.py:create_new_devices(),
server/scan/session_events.py:insert_events()).

quiet suppresses the outbound notification (evePendingAlertEmail=0) for New
Device/Connected/Down Reconnected events while still writing the Events row
(audit trail intact). It is creation-time-only ("decision A" in the PRD): a
device seeded quiet keeps devAlertDown=0/devAlertEvents=0 for its whole
lifecycle via the ordinary per-device settings, which then also suppresses
Device Down/Disconnected for free through the existing devAlertDown/
devAlertEvents gates - no separate code path needed for those two. Multiple
plugins reporting the same MAC resolve via most-restrictive-wins: any row
saying quiet suppresses, even if a sibling row says normal.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_db,
    make_current_scan_dict,
    insert_current_scan_row_from_dict,
    insert_device,
    minutes_ago,
    DummyDB,
)

from server.scan import device_handling  # noqa: E402
from server.scan.session_events import insert_events  # noqa: E402

MAC = "aa:bb:cc:dd:ee:01"


def _fake_get_setting_value(key, default=""):
    """NEWDEV_devAlertEvents/devAlertDown -> 1 (a distinguishable non-zero
    'normal' default), everything else -> a harmless empty-ish value so the
    rest of create_new_devices() doesn't choke on missing settings."""
    if key in ("NEWDEV_devAlertEvents", "NEWDEV_devAlertDown"):
        return 1
    if key in ("NEWDEV_devPresentLastScan", "NEWDEV_devIsArchived", "NEWDEV_devIsNew",
               "NEWDEV_devSkipRepeated", "NEWDEV_devScan", "NEWDEV_devFavorite",
               "NEWDEV_devLogEvents", "NEWDEV_devReqNicsOnline"):
        return 0
    return default


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    # safe_int() re-imports get_setting_value from `helper` on every call
    # (see server/db/db_helper.py) - patch the source module, not just
    # device_handling's already-bound reference, or the patch is a no-op there.
    monkeypatch.setattr("helper.get_setting_value", _fake_get_setting_value)
    monkeypatch.setattr("server.scan.device_handling.get_setting_value", _fake_get_setting_value)


def _device_row(db: DummyDB, mac: str):
    return db._conn.execute(
        "SELECT devAlertDown, devAlertEvents FROM Devices WHERE devMac = ?", (mac,)
    ).fetchone()


def _events(db: DummyDB, mac: str):
    return db._conn.execute(
        "SELECT eveEventType, evePendingAlertEmail FROM Events WHERE eveMac = ?", (mac,)
    ).fetchall()


class TestQuietCreationTimeSeeding:
    def test_quiet_new_device_gets_suppressed_event_and_seeded_alerts(self):
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanNotificationMode="quiet")
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        dev = _device_row(db, MAC)
        assert dev["devAlertDown"] == 0
        assert dev["devAlertEvents"] == 0

        events = _events(db, MAC)
        assert len(events) == 1
        assert events[0]["eveEventType"] == "New Device"
        assert events[0]["evePendingAlertEmail"] == 0

    def test_normal_new_device_uses_global_defaults(self):
        """Regression guard: default ('normal') behaves like today."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanNotificationMode="normal")
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        dev = _device_row(db, MAC)
        assert dev["devAlertDown"] == 1
        assert dev["devAlertEvents"] == 1

        events = _events(db, MAC)
        assert events[0]["evePendingAlertEmail"] == 1

    def test_most_restrictive_wins_across_plugins(self):
        """One plugin says normal, another says quiet for the same brand-new MAC."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanSourcePlugin="ARPSCAN", scanNotificationMode="normal")
        )
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanSourcePlugin="DOCKER", scanNotificationMode="quiet")
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        dev = _device_row(db, MAC)
        assert dev["devAlertDown"] == 0 and dev["devAlertEvents"] == 0, (
            "most-restrictive-wins: any row saying quiet must suppress, "
            "even though a sibling row for the same MAC says normal"
        )
        events = _events(db, MAC)
        assert len(events) == 1, "exactly one New Device event, not two conflicting ones"
        assert events[0]["evePendingAlertEmail"] == 0


class TestQuietIsCreationTimeOnlyNotOngoing:
    """Decision 'A': quiet only affects the creation moment. Reclassifying the
    plugin's row later must NOT retroactively change an already-seeded device's
    alert settings - there is no ongoing per-cycle re-derivation."""

    def test_reclassifying_to_normal_later_does_not_unsuppress(self):
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanNotificationMode="quiet")
        )
        db = DummyDB(conn)
        device_handling.create_new_devices(db)
        assert _device_row(db, MAC)["devAlertDown"] == 0

        # Next cycle: same device now reported as 'normal'. create_new_devices()
        # is a no-op for it (INSERT OR IGNORE, already exists) - nothing should
        # touch devAlertDown/devAlertEvents again.
        conn.execute("DELETE FROM CurrentScan")
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanNotificationMode="normal")
        )
        device_handling.create_new_devices(db)

        dev = _device_row(db, MAC)
        assert dev["devAlertDown"] == 0 and dev["devAlertEvents"] == 0, (
            "quiet must not be an ongoing/import-owned policy - once seeded, "
            "it's an ordinary per-device setting nothing re-derives"
        )


class TestQuietDeviceDownSuppressedForFree:
    """Because devAlertDown=0 was seeded at creation, insert_events()'s
    existing 'WHERE devAlertDown != 0' gate suppresses Device Down for this
    device with zero new code in insert_events() itself."""

    def test_quiet_device_going_absent_generates_no_down_event(self):
        conn = make_db()
        # Simulate a device already created quiet (devAlertDown/devAlertEvents=0),
        # previously present, now absent this cycle (CurrentScan left empty).
        insert_device(
            conn, MAC, alert_down=0, present_last_scan=1,
            last_connection=minutes_ago(60),
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType = 'Device Down'", (MAC,)
        ).fetchall()
        assert rows == [], "devAlertDown=0 (seeded via quiet) must suppress Device Down entirely"


class TestQuietReconnection:
    def test_quiet_reconnect_event_is_suppressed(self):
        conn = make_db()
        # last_ip must match make_current_scan_dict()'s default scanLastIP
        # (192.168.1.10) - a mismatch here also fires an unrelated "IP
        # Changed" event alongside "Connected", which isn't what this test
        # is isolating (found by a real test run, not caught in review).
        insert_device(
            conn, MAC, alert_down=1, present_last_scan=0,
            last_connection=minutes_ago(60), last_ip="192.168.1.10",
        )
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanNotificationMode="quiet")
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT eveEventType, evePendingAlertEmail FROM Events WHERE eveMac = ?", (MAC,)
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["evePendingAlertEmail"] == 0


class TestQuietSuppressesIpChangedToo:
    """IP Changed fires from a present CurrentScan row (unlike Device Down/
    Disconnected, which fire on absence and have no live value to read) - a
    live scanNotificationMode check is possible here and, per the decision
    recorded in the PRD's open issue, should apply additively on top of the
    device's own devAlertEvents toggle."""

    def test_quiet_row_suppresses_ip_changed(self):
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, last_ip="192.168.1.10")
        conn.execute("UPDATE Devices SET devAlertEvents = 1 WHERE devMac = ?", (MAC,))
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(
                MAC, scanLastIP="192.168.1.99", scanNotificationMode="quiet"
            )
        )
        db = DummyDB(conn)

        insert_events(db)

        row = conn.execute(
            "SELECT evePendingAlertEmail FROM Events WHERE eveMac = ? AND eveEventType = 'IP Changed'",
            (MAC,),
        ).fetchone()
        assert row is not None, "IP Changed event should still be logged (audit trail intact)"
        assert row["evePendingAlertEmail"] == 0

    def test_normal_row_with_alert_events_on_does_not_suppress(self):
        """Regression guard: existing devAlertEvents-driven behavior unchanged."""
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, last_ip="192.168.1.10")
        conn.execute("UPDATE Devices SET devAlertEvents = 1 WHERE devMac = ?", (MAC,))
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(
                MAC, scanLastIP="192.168.1.99", scanNotificationMode="normal"
            )
        )
        db = DummyDB(conn)

        insert_events(db)

        row = conn.execute(
            "SELECT evePendingAlertEmail FROM Events WHERE eveMac = ? AND eveEventType = 'IP Changed'",
            (MAC,),
        ).fetchone()
        assert row is not None
        assert row["evePendingAlertEmail"] == 1

    def test_devalertevents_off_still_suppresses_regardless_of_quiet(self):
        """The plugin-level quiet check is additive, not a replacement for
        the user's own toggle."""
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, last_ip="192.168.1.10")
        conn.execute("UPDATE Devices SET devAlertEvents = 0 WHERE devMac = ?", (MAC,))
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(
                MAC, scanLastIP="192.168.1.99", scanNotificationMode="normal"
            )
        )
        db = DummyDB(conn)

        insert_events(db)

        row = conn.execute(
            "SELECT evePendingAlertEmail FROM Events WHERE eveMac = ? AND eveEventType = 'IP Changed'",
            (MAC,),
        ).fetchone()
        assert row is not None
        assert row["evePendingAlertEmail"] == 0
