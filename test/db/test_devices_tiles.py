"""
Unit tests for get_sql_devices_tiles() (server/db/db_helper.py).

Tests verify that:
- Tile counts match hand-computed expectations for a known device set.
- The query evaluates DevicesView exactly once, not once per tile - a
  regression guard against reintroducing the 9-independent-scalar-subquery
  shape that re-ran DevicesView's own per-row cost (the devFlapping
  correlated EXISTS) 9 times per call.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_db,
    make_device_dict,
    insert_device_from_dict,
)

from db.db_helper import get_sql_devices_tiles  # noqa: E402


def _seed_devices(conn):
    """5 devices with distinct, known statuses."""
    devices = [
        make_device_dict("aa:bb:cc:dd:ee:01", devPresentLastScan=1, devIsArchived=0),
        make_device_dict("aa:bb:cc:dd:ee:02", devPresentLastScan=1, devIsArchived=0,
                          devFavorite=1),
        make_device_dict("aa:bb:cc:dd:ee:03", devPresentLastScan=0, devIsArchived=0),
        make_device_dict("aa:bb:cc:dd:ee:04", devPresentLastScan=0, devIsArchived=0,
                          devIsNew=1),
        make_device_dict("aa:bb:cc:dd:ee:05", devPresentLastScan=0, devIsArchived=1),
    ]
    for d in devices:
        insert_device_from_dict(conn, d)
    conn.commit()


class TestDevicesTilesCounts:
    def test_tile_counts_match_expected(self):
        conn = make_db()
        try:
            _seed_devices(conn)
            conn.execute(
                "INSERT INTO Settings (setKey, setValue) VALUES ('UI_MY_DEVICES', ?)",
                ("['online','offline']",),
            )
            conn.commit()

            row = conn.execute(get_sql_devices_tiles()).fetchone()
            cols = [d[0] for d in conn.execute(get_sql_devices_tiles()).description]
            tiles = dict(zip(cols, row))

            # devices 1,2 present -> connected; 3,4 present=0,archived=0 -> offline;
            # 5 archived -> excluded from active counts, counted only in archived/all_devices
            assert tiles["connected"] == 2
            assert tiles["offline"] == 2
            assert tiles["archived"] == 1
            assert tiles["favorites"] == 1
            assert tiles["new"] == 1
            assert tiles["all"] == 4          # active (non-archived) devices
            assert tiles["all_devices"] == 5  # every device, including archived
            # UI_MY_DEVICES = online+offline -> connected(2) + offline(2)
            assert tiles["my_devices"] == 4
        finally:
            conn.close()

    def test_empty_devicesview_returns_zero_not_null(self):
        """Regression guard: SUM(CASE...) over a zero-row DevicesView/Statuses
        cross join returns NULL per column, not 0 - COALESCE(..., 0) must be
        wrapped around every SUM-based tile, or a fresh install with no
        devices yet would see null tile counts instead of zeros."""
        conn = make_db()
        try:
            row = conn.execute(get_sql_devices_tiles()).fetchone()
            cols = [d[0] for d in conn.execute(get_sql_devices_tiles()).description]
            tiles = dict(zip(cols, row))

            # Iterate the query's own output columns rather than a separately
            # hardcoded key list, so this stays correct if a tile is renamed
            # or added/removed in get_sql_devices_tiles() itself.
            for key, value in tiles.items():
                assert value == 0, f"{key} was {value!r}, expected 0"
        finally:
            conn.close()

    def test_devicesview_evaluated_once_not_per_tile(self):
        """Regression guard: the query must not re-scan/re-evaluate DevicesView
        once per tile column (the bug this rewrite fixed). SQLite's planner
        flattens the view and reports the underlying 'Devices' table in the
        plan rather than 'DevicesView' itself - count SCAN/SEARCH operations
        on either name, not the literal string 'DevicesView'."""
        conn = make_db()
        try:
            _seed_devices(conn)
            conn.execute(
                "INSERT INTO Settings (setKey, setValue) VALUES ('UI_MY_DEVICES', ?)",
                ("['online']",),
            )
            conn.commit()

            plan = conn.execute(
                "EXPLAIN QUERY PLAN " + get_sql_devices_tiles()
            ).fetchall()
            plan_lines = [str(tuple(row)) for row in plan]
            device_scans = [
                line for line in plan_lines
                if ("SCAN Devices" in line or "SEARCH Devices" in line)
            ]

            assert len(device_scans) == 1, (
                f"expected exactly 1 scan/search of Devices(View), got "
                f"{len(device_scans)}: {plan_lines}"
            )
        finally:
            conn.close()
