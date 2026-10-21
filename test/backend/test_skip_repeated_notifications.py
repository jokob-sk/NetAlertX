"""
Tests for skip_repeated_notifications() UTC/localtime correctness.

Verifies that the cooldown comparison uses UTC on both sides, so that
devSkipRepeated works correctly regardless of the server's local timezone.

License: GNU GPLv3
"""

import sys
import os
import time
import unittest

# Make db_test_helpers importable from any working directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import make_db, minutes_ago, DummyDB  # noqa: E402

INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])


def _insert_device_with_cooldown(conn, mac, last_notification, skip_repeated):
    """Insert a Devices row with devLastNotification and devSkipRepeated set."""
    conn.execute(
        """
        INSERT INTO Devices
            (devMac, devLastNotification, devSkipRepeated,
             devAlertDown, devPresentLastScan, devIsArchived, devIsNew)
        VALUES (?, ?, ?, 1, 0, 0, 0)
        """,
        (mac, last_notification, skip_repeated),
    )


def _insert_pending_event(conn, mac):
    """Insert an Events row with evePendingAlertEmail=1 for the given MAC."""
    conn.execute(
        "INSERT INTO Events (eveMac, evePendingAlertEmail) VALUES (?, 1)",
        (mac,),
    )


def _get_flag(conn, mac):
    row = conn.execute(
        "SELECT evePendingAlertEmail FROM Events WHERE eveMac=?", (mac,)
    ).fetchone()
    return row[0] if row else None


class TestSkipRepeatedNotifications(unittest.TestCase):

    def test_recent_notification_suppresses_event(self):
        """A notification seconds ago should suppress the pending alert."""
        from messaging.reporting import skip_repeated_notifications

        conn = make_db()
        mac = "aa:bb:cc:dd:ee:01"
        _insert_device_with_cooldown(conn, mac, minutes_ago(0), skip_repeated=1)
        _insert_pending_event(conn, mac)
        conn.commit()

        skip_repeated_notifications(DummyDB(conn))

        self.assertEqual(
            _get_flag(conn, mac),
            0,
            "Event should be suppressed: last notification is recent (0 min ago), cooldown 1 h",
        )

    def test_old_notification_does_not_suppress(self):
        """A notification older than devSkipRepeated should NOT suppress the event."""
        from messaging.reporting import skip_repeated_notifications

        conn = make_db()
        mac = "aa:bb:cc:dd:ee:02"
        _insert_device_with_cooldown(conn, mac, minutes_ago(120), skip_repeated=1)
        _insert_pending_event(conn, mac)
        conn.commit()

        skip_repeated_notifications(DummyDB(conn))

        self.assertEqual(
            _get_flag(conn, mac),
            1,
            "Event should NOT be suppressed: last notification was 2 h ago, cooldown 1 h",
        )

    def test_utc_stored_timestamp_within_cooldown_suppresses(self):
        """
        Regression test for the UTC/localtime bug.

        A UTC timestamp 20 minutes ago with a 2-hour cooldown must be
        suppressed.  With the old 'localtime' modifier the comparison was
        inflated by the UTC offset (e.g. +7200 s for UTC+2), which made
        the cooldown appear expired even for genuinely-recent notifications.
        """
        from messaging.reporting import skip_repeated_notifications

        conn = make_db()
        mac = "aa:bb:cc:dd:ee:03"
        _insert_device_with_cooldown(conn, mac, minutes_ago(20), skip_repeated=2)
        _insert_pending_event(conn, mac)
        conn.commit()

        skip_repeated_notifications(DummyDB(conn))

        self.assertEqual(
            _get_flag(conn, mac),
            0,
            "Event should be suppressed: only 20 min elapsed, cooldown 2 h. "
            "Failure here indicates the localtime UTC-offset bug is still present.",
        )

    def test_zero_skip_repeated_never_suppresses(self):
        """devSkipRepeated=0 should never suppress notifications."""
        from messaging.reporting import skip_repeated_notifications

        conn = make_db()
        mac = "aa:bb:cc:dd:ee:04"
        _insert_device_with_cooldown(conn, mac, minutes_ago(0), skip_repeated=0)
        _insert_pending_event(conn, mac)
        conn.commit()

        skip_repeated_notifications(DummyDB(conn))

        self.assertEqual(
            _get_flag(conn, mac),
            1,
            "Event should NOT be suppressed when devSkipRepeated=0",
        )


if __name__ == "__main__":
    unittest.main()
