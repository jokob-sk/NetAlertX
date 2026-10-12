"""
Tests for notification_sections.py's SQL_TEMPLATES against a pending event
for a MAC that no longer has a Devices row (the device was deleted while an
event was still waiting to be reported).

Events_Devices (server/db/db_upgrade.py) is Events LEFT JOIN Devices, so a
deleted device's orphaned pending event still surfaces through it with every
Devices-sourced column NULL. Nothing else in the notification pipeline
excludes it: the "disable if device opted out" pre-filters in
get_notifications() and skip_repeated_notifications() both gate via
`eveMac IN (SELECT devMac FROM Devices WHERE ...)`, which can never match a
MAC with no Devices row at all.

Deleting a device must not delete its Events rows (Events is a persistent,
append-only audit trail read directly by the global events.php page, not
just the per-device tab) - so the fix is at the query level, not by cleaning
up Events on delete.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from messaging.notification_sections import SQL_TEMPLATES  # noqa: E402
from db_test_helpers import make_db, insert_device, now_utc  # noqa: E402

EXISTING_MAC = "aa:bb:cc:dd:ee:01"
DELETED_MAC = "aa:bb:cc:dd:ee:02"


def _insert_event(conn, mac, event_type, minutes_old=0):
    cur = conn.cursor()
    event_time = now_utc() if minutes_old == 0 else _minutes_ago(minutes_old)
    cur.execute(
        """INSERT INTO Events
           (eveMac, eveIp, eveDateTime, eveEventType, eveAdditionalInfo, evePendingAlertEmail)
           VALUES (?, '192.168.1.1', ?, ?, '', 1)""",
        (mac, event_time, event_type),
    )
    conn.commit()


def _minutes_ago(n):
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) - timedelta(minutes=n)).strftime("%Y-%m-%d %H:%M:%S")


def _setup(conn):
    """EXISTING_MAC has a Devices row; DELETED_MAC does not (simulates a
    device deleted while it still had a pending, unreported event)."""
    cur = conn.cursor()
    insert_device(cur, EXISTING_MAC, alert_down=1)
    conn.commit()


def _run_template(conn, section, **format_vars):
    sql = SQL_TEMPLATES[section].format(condition="", **format_vars)
    return conn.execute(sql).fetchall()


class TestNewDevicesExcludesOrphanedEvent:
    def test_orphaned_mac_excluded_existing_mac_kept(self):
        conn = make_db()
        _setup(conn)
        _insert_event(conn, EXISTING_MAC, "New Device")
        _insert_event(conn, DELETED_MAC, "New Device")

        rows = _run_template(conn, "new_devices")
        macs = {r["eveMac"] for r in rows}

        assert EXISTING_MAC in macs
        assert DELETED_MAC not in macs


class TestDownDevicesExcludesOrphanedEvent:
    def test_orphaned_mac_excluded_existing_mac_kept(self):
        conn = make_db()
        _setup(conn)
        _insert_event(conn, EXISTING_MAC, "Device Down", minutes_old=10)
        _insert_event(conn, DELETED_MAC, "Device Down", minutes_old=10)

        rows = _run_template(conn, "down_devices", alert_down_minutes=0)
        macs = {r["eveMac"] for r in rows}

        assert EXISTING_MAC in macs
        assert DELETED_MAC not in macs


class TestDownReconnectedExcludesOrphanedEvent:
    def test_orphaned_mac_excluded_existing_mac_kept(self):
        conn = make_db()
        _setup(conn)
        _insert_event(conn, EXISTING_MAC, "Down Reconnected")
        _insert_event(conn, DELETED_MAC, "Down Reconnected")

        rows = _run_template(conn, "down_reconnected")
        macs = {r["eveMac"] for r in rows}

        assert EXISTING_MAC in macs
        assert DELETED_MAC not in macs


class TestEventsExcludesOrphanedEvent:
    def test_orphaned_mac_excluded_existing_mac_kept(self):
        conn = make_db()
        _setup(conn)
        _insert_event(conn, EXISTING_MAC, "Connected")
        _insert_event(conn, DELETED_MAC, "Connected")

        rows = _run_template(
            conn, "events",
            event_types="'Connected', 'Down Reconnected', 'Disconnected','IP Changed'",
        )
        macs = {r["eveMac"] for r in rows}

        assert EXISTING_MAC in macs
        assert DELETED_MAC not in macs
