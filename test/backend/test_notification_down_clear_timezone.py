"""
Tests for NotificationInstance.clearPendingEmailFlag()'s UTC/localtime
correctness (netalertx/NetAlertX#1851).

eveDateTime is always stored in UTC (utils.datetime_utils.timeNowUTC() is the
single source of truth for DB timestamps). The down_devices selection query
in notification_sections.py compares it against a plain
`datetime('now', '-N minutes')` cutoff, i.e. UTC vs UTC. clearPendingEmailFlag()
must use the same UTC-only cutoff to clear the flag it set - applying an
additional timezone-offset modifier shifts the clear cutoff by the server's
UTC offset, so west-of-UTC zones leave old 'Device Down' events flagged for
hours (repeatedly re-sent, never cleared) and east-of-UTC zones would clear
them too early.

License: GNU GPLv3
"""

import sys
import os
import types
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_db,
    insert_device,
    minutes_ago,
    DummyDB,
    CREATE_PLUGINS_EVENTS,
)

INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

import conf  # noqa: E402

# json2table isn't needed by this test (only finalize_html() uses it) and
# isn't always installed outside the container; stub it for the duration of
# the import below, then drop it so it doesn't leak into other test files.
_json2table_was_stubbed = "json2table" not in sys.modules
if _json2table_was_stubbed:
    _stub = types.ModuleType("json2table")
    _stub.convert = lambda *a, **k: ""
    sys.modules["json2table"] = _stub

from models.notification_instance import NotificationInstance  # noqa: E402

if _json2table_was_stubbed:
    sys.modules.pop("json2table", None)


def _make_db():
    """make_db() plus Plugins_Events, which clearPendingEmailFlag() always
    clears at the end via clearPluginEvents()."""
    conn = make_db()
    conn.execute(CREATE_PLUGINS_EVENTS)
    conn.commit()
    return conn


def _insert_down_event(conn, mac, minutes_old):
    """Insert a pending 'Device Down' Events row *minutes_old* minutes ago (UTC)."""
    conn.execute(
        """
        INSERT INTO Events (eveMac, eveDateTime, eveEventType, evePendingAlertEmail)
        VALUES (?, ?, 'Device Down', 1)
        """,
        (mac, minutes_ago(minutes_old)),
    )


def _get_flag(conn, mac):
    row = conn.execute(
        "SELECT evePendingAlertEmail FROM Events WHERE eveMac=?", (mac,)
    ).fetchone()
    return row[0] if row else None


def _clear_with_tz(conn, alert_down_minutes, tz_name):
    """Instantiate NotificationInstance without running its real __init__
    (which needs a live settings DB/Logger) and call clearPendingEmailFlag()
    with conf.tz set to tz_name, restoring the previous conf.tz afterward."""
    original_tz = getattr(conf, "tz", None)
    conf.tz = ZoneInfo(tz_name) if tz_name else None
    try:
        ni = NotificationInstance.__new__(NotificationInstance)
        ni.db = DummyDB(conn)
        with patch(
            "models.notification_instance.get_setting_value",
            return_value=str(alert_down_minutes),
        ):
            ni.clearPendingEmailFlag()
    finally:
        conf.tz = original_tz


class TestClearPendingEmailFlagTimezone(unittest.TestCase):

    def test_old_down_event_clears_west_of_utc(self):
        """
        Regression test for the UTC/tz-offset bug (#1851).

        10 minutes old, 5-minute cutoff: the down_devices selection query
        would already be resending this event every loop (UTC-only check).
        clearPendingEmailFlag() must clear it too. Under the old
        tz-offset-applied query, America/Los_Angeles (UTC-7/-8) pushes the
        clear cutoff ~7-8 hours further into the past, so a 10-minute-old
        event incorrectly stays flagged and keeps getting resent.
        """
        conn = _make_db()
        mac = "aa:bb:cc:dd:ee:01"
        insert_device(conn, mac, alert_down=1)
        _insert_down_event(conn, mac, minutes_old=10)
        conn.commit()

        _clear_with_tz(conn, alert_down_minutes=5, tz_name="America/Los_Angeles")

        self.assertEqual(
            _get_flag(conn, mac),
            0,
            "10-minute-old Device Down event with a 5-minute cutoff must be "
            "cleared regardless of server timezone.",
        )

    def test_recent_down_event_stays_pending(self):
        """A down event younger than the cutoff must stay pending (sanity
        check that the fix isn't simply disabling the time filter)."""
        conn = _make_db()
        mac = "aa:bb:cc:dd:ee:02"
        insert_device(conn, mac, alert_down=1)
        _insert_down_event(conn, mac, minutes_old=2)
        conn.commit()

        _clear_with_tz(conn, alert_down_minutes=5, tz_name="America/Los_Angeles")

        self.assertEqual(
            _get_flag(conn, mac),
            1,
            "2-minute-old Device Down event with a 5-minute cutoff must stay pending.",
        )

    def test_recent_down_event_does_not_clear_early_east_of_utc(self):
        """
        Mirror check east of UTC (#1851 notes the opposite symptom there):
        a positive tz offset shifts the clear cutoff *forward* in time
        (e.g. Asia/Kolkata's +05:30 pushes 'now - 5 minutes' to roughly
        'now + 5h25m'), which would clear almost any already-pending event
        immediately, regardless of whether NTFPRCS_alert_down_time has
        actually elapsed.
        """
        conn = _make_db()
        mac = "aa:bb:cc:dd:ee:03"
        insert_device(conn, mac, alert_down=1)
        _insert_down_event(conn, mac, minutes_old=1)
        conn.commit()

        _clear_with_tz(conn, alert_down_minutes=5, tz_name="Asia/Kolkata")

        self.assertEqual(
            _get_flag(conn, mac),
            1,
            "1-minute-old Device Down event with a 5-minute cutoff must stay "
            "pending regardless of server timezone.",
        )


if __name__ == "__main__":
    unittest.main()
