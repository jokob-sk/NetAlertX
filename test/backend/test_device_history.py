"""
Unit tests for the DevicesHistory feature.

Tests cover:
  - AFTER INSERT trigger: new device logs tracked fields with oldValue=None
  - AFTER UPDATE trigger: field change is logged with correct attribution
  - AFTER UPDATE trigger: no-op when DEV_HIST_DAYS=0
  - AFTER UPDATE trigger: field not in DEV_HIST_TRACKED is not logged
  - DevicesHistoryInstance.get_grouped_history: groups and paginates correctly
  - DevicesHistoryInstance.get_all_grouped_history: returns multi-device results
  - DevicesHistoryInstance.get_available_filter_values: distinct values returned
  - DevicesHistoryInstance.get_total_group_count: correct count
  - DevicesHistoryInstance.prune_history: deletes old rows, skips at days=0
"""

import sys
import os
import unittest
import unittest.mock
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db_test_helpers import make_history_db


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

_TRACKED = "['devName', 'devVendor', 'devLastIP', 'devNameSource']"

_INSERT_SQL = """
    INSERT INTO Devices
        (devMac, devGUID, devName, devVendor, devLastIP, devNameSource,
         devAlertDown, devPresentLastScan, devIsNew, devIsArchived,
         devFirstConnection, devLastConnection)
    VALUES (?, ?, ?, ?, ?, ?, 0, 1, 0, 0,
            datetime('now'), datetime('now'))
"""


def _insert_device(conn, mac, guid, name="Router", vendor="Cisco",
                   last_ip="192.168.1.1", name_source="ARPSCAN"):
    conn.execute(_INSERT_SQL, (mac, guid, name, vendor, last_ip, name_source))
    conn.commit()


def _history_rows(conn, guid=None, column=None):
    """Fetch DevicesHistory rows, optionally filtered."""
    clauses = []
    params = []
    if guid:
        clauses.append("devGUID = ?")
        params.append(guid)
    if column:
        clauses.append("changedColumn = ?")
        params.append(column)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return conn.execute(
        f"SELECT * FROM DevicesHistory {where} ORDER BY id", params
    ).fetchall()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestInsertTrigger(unittest.TestCase):
    """AFTER INSERT trigger fires for tracked fields on new device creation."""

    def setUp(self):
        self.conn = make_history_db(tracked=_TRACKED)

    def tearDown(self):
        self.conn.close()

    def test_tracked_fields_logged_on_insert(self):
        _insert_device(self.conn, "aa:bb:cc:00:00:01", "guid-insert-1",
                       name="Router", vendor="Cisco")
        rows = _history_rows(self.conn, guid="guid-insert-1")
        columns_logged = {r["changedColumn"] for r in rows}
        # devName and devVendor should always be logged (non-NULL in INSERT)
        self.assertIn("devName", columns_logged)
        self.assertIn("devVendor", columns_logged)

    def test_old_value_is_null_on_insert(self):
        _insert_device(self.conn, "aa:bb:cc:00:00:02", "guid-insert-2")
        rows = _history_rows(self.conn, guid="guid-insert-2", column="devName")
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["oldValue"])
        self.assertEqual(rows[0]["newValue"], "Router")

    def test_source_attribution_from_source_field(self):
        _insert_device(self.conn, "aa:bb:cc:00:00:03", "guid-insert-3",
                       name_source="ARPSCAN")
        rows = _history_rows(self.conn, guid="guid-insert-3", column="devName")
        self.assertEqual(rows[0]["changedBy"], "ARPSCAN")

    def test_untracked_field_not_logged(self):
        # devOwner is not in _TRACKED so its change must not appear
        _insert_device(self.conn, "aa:bb:cc:00:00:04", "guid-insert-4")
        rows = _history_rows(self.conn, guid="guid-insert-4")
        logged_cols = {r["changedColumn"] for r in rows}
        self.assertNotIn("devOwner", logged_cols)


class TestUpdateTrigger(unittest.TestCase):
    """AFTER UPDATE trigger fires with correct values and attribution."""

    def setUp(self):
        self.conn = make_history_db(tracked=_TRACKED)
        _insert_device(self.conn, "aa:bb:cc:01:00:01", "guid-upd-1")

    def tearDown(self):
        self.conn.close()

    def test_name_change_logged(self):
        self.conn.execute(
            "UPDATE Devices SET devName='My Router', devNameSource='USER' WHERE devGUID=?",
            ("guid-upd-1",)
        )
        self.conn.commit()
        rows = _history_rows(self.conn, guid="guid-upd-1", column="devName")
        # Two rows: INSERT (old=None) and UPDATE (old=Router)
        update_rows = [r for r in rows if r["oldValue"] is not None]
        self.assertEqual(len(update_rows), 1)
        self.assertEqual(update_rows[0]["oldValue"], "Router")
        self.assertEqual(update_rows[0]["newValue"], "My Router")
        self.assertEqual(update_rows[0]["changedBy"], "USER")

    def test_plugin_attribution(self):
        self.conn.execute(
            "UPDATE Devices SET devVendor='Netgear', devVendorSource='VNDRPDT' WHERE devGUID=?",
            ("guid-upd-1",)
        )
        self.conn.commit()
        rows = _history_rows(self.conn, guid="guid-upd-1", column="devVendor")
        update_rows = [r for r in rows if r["oldValue"] is not None]
        self.assertEqual(update_rows[0]["changedBy"], "VNDRPDT")

    def test_no_change_no_row(self):
        before = len(_history_rows(self.conn, guid="guid-upd-1"))
        # Update with same value
        self.conn.execute(
            "UPDATE Devices SET devName='Router' WHERE devGUID=?",
            ("guid-upd-1",)
        )
        self.conn.commit()
        after = len(_history_rows(self.conn, guid="guid-upd-1"))
        self.assertEqual(before, after)


class TestDisabledGuard(unittest.TestCase):
    """AFTER UPDATE trigger is silent when DEV_HIST_DAYS=0."""

    def test_no_rows_when_disabled(self):
        conn = make_history_db(dev_hist_days=0, tracked=_TRACKED)
        _insert_device(conn, "aa:bb:cc:02:00:01", "guid-dis-1")
        conn.execute(
            "UPDATE Devices SET devName='Changed', devNameSource='USER' WHERE devGUID=?",
            ("guid-dis-1",)
        )
        conn.commit()
        rows = _history_rows(conn)
        conn.close()
        self.assertEqual(len(rows), 0)


class TestDevicesHistoryInstance(unittest.TestCase):
    """Tests for DevicesHistoryInstance query/prune methods."""

    def setUp(self):
        self.conn = make_history_db(tracked=_TRACKED)

        # `device_history_instance` uses `from database import get_temp_db_connection`
        # which creates a local reference.  We must patch THAT namespace, not the
        # database module attribute.
        import models.device_history_instance as _mod

        _real = self.conn

        class _NoClose:
            def execute(self, *a, **kw): return _real.execute(*a, **kw)
            def cursor(self): return _real.cursor()
            def commit(self): _real.commit()
            def rollback(self): _real.rollback()
            def close(self): pass  # intentional no-op

        self._patcher = unittest.mock.patch.object(
            _mod, "get_temp_db_connection", return_value=_NoClose()
        )
        self._patcher.start()

        _insert_device(self.conn, "bb:cc:dd:00:00:01", "guid-q-1",
                       name="Alpha", vendor="Cisco")
        _insert_device(self.conn, "bb:cc:dd:00:00:02", "guid-q-2",
                       name="Beta", vendor="HP")
        # One user update on guid-q-1
        self.conn.execute(
            "UPDATE Devices SET devName='Alpha v2', devNameSource='USER' WHERE devGUID='guid-q-1'"
        )
        self.conn.commit()

        from models.device_history_instance import DevicesHistoryInstance
        self.h = DevicesHistoryInstance()

    def tearDown(self):
        self._patcher.stop()
        self.conn.close()

    def test_get_grouped_history_returns_groups(self):
        groups = self.h.get_grouped_history("guid-q-1")
        self.assertGreater(len(groups), 0)
        for g in groups:
            self.assertEqual(g["devGUID"], "guid-q-1")
            self.assertIn("timestamp", g)
            self.assertIn("changedBy", g)
            self.assertIsInstance(g["changes"], list)

    def test_changedcolumn_filter(self):
        groups = self.h.get_grouped_history("guid-q-1", changedColumn="devName")
        for g in groups:
            cols = [c["changedColumn"] for c in g["changes"]]
            self.assertIn("devName", cols)

    def test_changedby_filter(self):
        groups = self.h.get_grouped_history("guid-q-1", changedBy="USER")
        self.assertGreater(len(groups), 0)
        for g in groups:
            self.assertEqual(g["changedBy"], "USER")

    def test_pagination(self):
        all_groups = self.h.get_grouped_history("guid-q-1")
        if len(all_groups) < 2:
            self.skipTest("Not enough groups to test pagination")
        page1 = self.h.get_grouped_history("guid-q-1", limit=1, offset=0)
        page2 = self.h.get_grouped_history("guid-q-1", limit=1, offset=1)
        self.assertEqual(len(page1), 1)
        self.assertEqual(len(page2), 1)
        # Pages must represent distinct groups (same key = (timestamp, changedBy, devGUID))
        key1 = (page1[0]["timestamp"], page1[0]["changedBy"])
        key2 = (page2[0]["timestamp"], page2[0]["changedBy"])
        self.assertNotEqual(key1, key2)

    def test_get_all_grouped_history(self):
        groups = self.h.get_all_grouped_history()
        guids = {g["devGUID"] for g in groups}
        self.assertIn("guid-q-1", guids)
        self.assertIn("guid-q-2", guids)

    def test_get_available_filter_values(self):
        filters = self.h.get_available_filter_values("guid-q-1")
        self.assertIn("changedBy", filters)
        self.assertIn("changedColumn", filters)
        self.assertIsInstance(filters["changedBy"], list)
        self.assertIsInstance(filters["changedColumn"], list)
        self.assertGreater(len(filters["changedColumn"]), 0)

    def test_get_total_group_count(self):
        total = self.h.get_total_group_count("guid-q-1")
        groups = self.h.get_grouped_history("guid-q-1", limit=1000)
        self.assertEqual(total, len(groups))

    def test_prune_history_zero_skips(self):
        deleted = self.h.prune_history(0)
        self.assertEqual(deleted, 0)

    def test_prune_history_removes_old_rows(self):
        # Manually insert an old row
        self.conn.execute(
            """INSERT INTO DevicesHistory (devGUID, changedColumn, oldValue, newValue, changedBy, timestamp)
               VALUES ('guid-q-1', 'devName', 'old', 'new', 'system', datetime('now', '-30 days'))"""
        )
        self.conn.commit()
        old_count = self.conn.execute("SELECT COUNT(*) FROM DevicesHistory").fetchone()[0]
        deleted = self.h.prune_history(14)
        new_count = self.conn.execute("SELECT COUNT(*) FROM DevicesHistory").fetchone()[0]
        self.assertGreater(deleted, 0)
        self.assertLess(new_count, old_count)

    def test_prune_history_keeps_recent_rows(self):
        before = self.conn.execute("SELECT COUNT(*) FROM DevicesHistory").fetchone()[0]
        # prune with 365 days — nothing should be deleted from a fresh test DB
        deleted = self.h.prune_history(365)
        after = self.conn.execute("SELECT COUNT(*) FROM DevicesHistory").fetchone()[0]
        self.assertEqual(deleted, 0)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
