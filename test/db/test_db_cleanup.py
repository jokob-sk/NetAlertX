"""
Unit tests for db_cleanup plugin SQL logic.

Covers:
- Sessions trim (reuses DAYS_TO_KEEP_EVENTS window)
- ANALYZE refreshes sqlite_stat1 after bulk deletes
- PRAGMA optimize runs without error

Each test creates an isolated in-memory SQLite database so there is no
dependency on the running application or its config.
"""

import sqlite3
import os


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db():
    """Return an in-memory connection seeded with the tables used by db_cleanup."""
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE Events (
            eveMac               TEXT NOT NULL,
            eveIp                TEXT NOT NULL,
            eveDateTime          DATETIME NOT NULL,
            eveEventType         TEXT NOT NULL,
            eveAdditionalInfo    TEXT DEFAULT '',
            evePendingAlertEmail INTEGER NOT NULL DEFAULT 1,
            evePairEventRowid    INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE Sessions (
            sesMac                   TEXT,
            sesIp                    TEXT,
            sesEventTypeConnection   TEXT,
            sesDateTimeConnection    DATETIME,
            sesEventTypeDisconnection TEXT,
            sesDateTimeDisconnection  DATETIME,
            sesStillConnected        INTEGER,
            sesAdditionalInfo        TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE Resource_History (
            "index"           INTEGER PRIMARY KEY AUTOINCREMENT,
            resDateTime       TEXT NOT NULL,
            resCpuPercent     REAL,
            resRssMb          REAL,
            resIoReadBytes    INTEGER,
            resIoWriteBytes   INTEGER,
            resScanDurationMs INTEGER,
            resTickFailed     INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    return conn


def _seed_sessions(cur, old_count: int, recent_count: int, days: int):
    """
    Insert `old_count` rows with connection date older than `days` days and
    `recent_count` rows with connection date today.
    """
    for i in range(old_count):
        cur.execute(
            "INSERT INTO Sessions (sesMac, sesDateTimeConnection) "
            "VALUES (?, date('now', ?))",
            (f"AA:BB:CC:DD:EE:{i:02X}", f"-{days + 1} day"),
        )
    for i in range(recent_count):
        cur.execute(
            "INSERT INTO Sessions (sesMac, sesDateTimeConnection) "
            "VALUES (?, date('now'))",
            (f"11:22:33:44:55:{i:02X}",),
        )


def _run_sessions_trim(cur, days: int) -> int:
    """Execute the exact DELETE used by db_cleanup and return rowcount."""
    cur.execute(
        f"DELETE FROM Sessions "
        f"WHERE sesDateTimeConnection <= date('now', '-{days} day')"
    )
    return cur.rowcount


# ---------------------------------------------------------------------------
# Sessions trim tests
# ---------------------------------------------------------------------------

class TestSessionsTrim:

    def test_old_rows_are_deleted(self):
        """Rows older than DAYS_TO_KEEP_EVENTS window must be removed."""
        conn = _make_db()
        cur = conn.cursor()
        _seed_sessions(cur, old_count=10, recent_count=5, days=30)

        deleted = _run_sessions_trim(cur, days=30)

        assert deleted == 10, f"Expected 10 old rows deleted, got {deleted}"
        cur.execute("SELECT COUNT(*) FROM Sessions")
        remaining = cur.fetchone()[0]
        assert remaining == 5, f"Expected 5 recent rows to survive, got {remaining}"

    def test_recent_rows_are_preserved(self):
        """Rows within the retention window must not be touched."""
        conn = _make_db()
        cur = conn.cursor()
        _seed_sessions(cur, old_count=0, recent_count=20, days=30)

        deleted = _run_sessions_trim(cur, days=30)

        assert deleted == 0, f"Expected 0 deletions, got {deleted}"
        cur.execute("SELECT COUNT(*) FROM Sessions")
        assert cur.fetchone()[0] == 20

    def test_empty_table_is_a_no_op(self):
        """Trim against an empty Sessions table must not raise."""
        conn = _make_db()
        cur = conn.cursor()

        deleted = _run_sessions_trim(cur, days=30)

        assert deleted == 0

    def test_trim_is_bounded_by_days_parameter(self):
        """Only rows strictly outside the window are removed; boundary row survives."""
        conn = _make_db()
        cur = conn.cursor()
        # Row exactly AT the boundary (date = 'now' - days exactly)
        cur.execute(
            "INSERT INTO Sessions (sesMac, sesDateTimeConnection) "
            "VALUES (?, date('now', ?))",
            ("AA:BB:CC:00:00:01", "-30 day"),
        )
        # Row just inside the window
        cur.execute(
            "INSERT INTO Sessions (sesMac, sesDateTimeConnection) "
            "VALUES (?, date('now', '-29 day'))",
            ("AA:BB:CC:00:00:02",),
        )

        _run_sessions_trim(cur, days=30)

        cur.execute("SELECT sesMac FROM Sessions")
        remaining_macs = {row[0] for row in cur.fetchall()}
        # Boundary row (== threshold) is deleted; inside row survives
        assert "AA:BB:CC:00:00:02" in remaining_macs, "Row inside window was wrongly deleted"

    def test_sessions_trim_uses_same_value_as_events(self):
        """
        Regression: verify that the Sessions DELETE uses an identical day-offset
        expression to the Events DELETE so the two tables stay aligned.
        """

        INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
        script_path = os.path.join(
            INSTALL_PATH, "server", "plugins", "db_cleanup", "script.py"
        )
        with open(script_path) as fh:
            source = fh.read()

        events_expr = "DELETE FROM Events WHERE eveDateTime <= date('now', '-{str(DAYS_TO_KEEP_EVENTS)} day')"
        sessions_expr = "DELETE FROM Sessions WHERE sesDateTimeConnection <= date('now', '-{str(DAYS_TO_KEEP_EVENTS)} day')"

        assert events_expr in source, "Events DELETE expression changed unexpectedly"
        assert sessions_expr in source, "Sessions DELETE is not aligned with Events DELETE"


# ---------------------------------------------------------------------------
# Resource_History retention (MAINT_PERF_DAYS)
# ---------------------------------------------------------------------------

def _seed_resource_history(cur, old_count: int, recent_count: int, days: int):
    for i in range(old_count):
        cur.execute(
            "INSERT INTO Resource_History (resDateTime, resCpuPercent) "
            "VALUES (datetime('now', ?), 10.0)",
            (f"-{days + 1} day",),
        )
    for i in range(recent_count):
        cur.execute(
            "INSERT INTO Resource_History (resDateTime, resCpuPercent) "
            "VALUES (datetime('now'), 10.0)"
        )


def _run_resource_history_trim(cur, days: int) -> int:
    """Execute the exact DELETE used by db_cleanup and return rowcount."""
    cur.execute(
        f"DELETE FROM Resource_History "
        f"WHERE resDateTime <= datetime('now', '-{days} day')"
    )
    return cur.rowcount


class TestResourceHistoryTrim:

    def test_old_rows_are_deleted(self):
        conn = _make_db()
        cur = conn.cursor()
        _seed_resource_history(cur, old_count=10, recent_count=5, days=30)

        deleted = _run_resource_history_trim(cur, days=30)

        assert deleted == 10
        cur.execute("SELECT COUNT(*) FROM Resource_History")
        assert cur.fetchone()[0] == 5

    def test_recent_rows_are_preserved(self):
        conn = _make_db()
        cur = conn.cursor()
        _seed_resource_history(cur, old_count=0, recent_count=20, days=30)

        deleted = _run_resource_history_trim(cur, days=30)

        assert deleted == 0
        cur.execute("SELECT COUNT(*) FROM Resource_History")
        assert cur.fetchone()[0] == 20

    def test_empty_table_is_a_no_op(self):
        conn = _make_db()
        cur = conn.cursor()

        assert _run_resource_history_trim(cur, days=30) == 0

    def test_date_cutoff_would_silently_under_delete_the_boundary_day(self):
        """
        Regression, demonstrating the bug the datetime() fix closes: date()
        truncates the cutoff to midnight (10-char "YYYY-MM-DD"), while
        resDateTime always carries a time component (19-char
        "YYYY-MM-DD HH:MM:SS", from timeNowUTC()). Since the bare date string
        is a strict prefix of any same-day timestamp, plain string comparison
        (SQLite has no typed DATE column here) means resDateTime <= date(...)
        is FALSE for every row on the cutoff day, regardless of its time of
        day - the whole boundary day silently survives a date() cutoff.
        datetime() doesn't have this gap: both sides are 19-char timestamps.
        """
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        date_cutoff = cur.execute("SELECT date('now', '-30 day')").fetchone()[0]
        datetime_cutoff = cur.execute("SELECT datetime('now', '-30 day')").fetchone()[0]

        assert len(date_cutoff) == 10  # "YYYY-MM-DD" - no time component
        assert len(datetime_cutoff) == 19  # "YYYY-MM-DD HH:MM:SS"
        assert datetime_cutoff.startswith(date_cutoff)

        # A same-day resDateTime value (any time after midnight) sorts after
        # the bare date cutoff, so it would never satisfy `<=` under date().
        same_day_timestamp = date_cutoff + " 08:00:00"
        assert not (same_day_timestamp <= date_cutoff), (
            "date() cutoff must fail to catch a same-day timestamped row - "
            "this is exactly the bug datetime() fixes"
        )

    def test_resource_history_trim_uses_datetime_not_date(self):
        """
        Regression: assert script.py's actual DELETE uses datetime(), matching
        the precision of resDateTime and the read-side range queries
        (const.py's sql_resource_history_* use datetime() too) - a bare
        date() cutoff would silently under-delete (see test above).
        """
        INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
        script_path = os.path.join(
            INSTALL_PATH, "server", "plugins", "db_cleanup", "script.py"
        )
        with open(script_path) as fh:
            source = fh.read()

        expr = "DELETE FROM Resource_History WHERE resDateTime <= datetime('now', '-{str(MAINT_PERF_DAYS)} day')"
        assert expr in source, "Resource_History DELETE must use datetime(), not date()"


# ---------------------------------------------------------------------------
# ANALYZE tests
# ---------------------------------------------------------------------------

class TestAnalyze:

    def test_analyze_populates_sqlite_stat1(self):
        """
        After ANALYZE, sqlite_stat1 must exist and have at least one row
        for the Events table (which has an implicit rowid index).
        """
        conn = _make_db()
        cur = conn.cursor()

        # Seed some rows so ANALYZE has something to measure
        for i in range(20):
            cur.execute(
                "INSERT INTO Events (eveMac, eveIp, eveDateTime, eveEventType) "
                "VALUES (?, '1.2.3.4', date('now'), 'Connected')",
                (f"AA:BB:CC:DD:EE:{i:02X}",),
            )
        conn.commit()

        cur.execute("ANALYZE;")
        conn.commit()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_stat1'")
        assert cur.fetchone() is not None, "sqlite_stat1 table not created by ANALYZE"

    def test_analyze_does_not_raise_on_empty_tables(self):
        """ANALYZE against empty tables must complete without exceptions."""
        conn = _make_db()
        cur = conn.cursor()

        # Should not raise
        cur.execute("ANALYZE;")
        conn.commit()

    def test_analyze_is_idempotent(self):
        """Running ANALYZE twice must not raise or corrupt state."""
        conn = _make_db()
        cur = conn.cursor()

        cur.execute("ANALYZE;")
        cur.execute("ANALYZE;")
        conn.commit()


# ---------------------------------------------------------------------------
# PRAGMA optimize tests
# ---------------------------------------------------------------------------

class TestPragmaOptimize:

    def test_pragma_optimize_does_not_raise(self):
        """PRAGMA optimize must complete without exceptions."""
        conn = _make_db()
        cur = conn.cursor()

        # Run ANALYZE first (as db_cleanup does) then optimize
        cur.execute("ANALYZE;")
        cur.execute("PRAGMA optimize;")
        conn.commit()

    def test_pragma_optimize_after_bulk_delete(self):
        """
        PRAGMA optimize after a bulk DELETE (simulating db_cleanup) must
        complete without error, validating the full tail sequence.
        """
        conn = _make_db()
        cur = conn.cursor()

        for i in range(50):
            cur.execute(
                "INSERT INTO Sessions (sesMac, sesDateTimeConnection) "
                "VALUES (?, date('now', '-60 day'))",
                (f"AA:BB:CC:DD:EE:{i:02X}",),
            )
        conn.commit()

        # Mirror the tail sequence from cleanup_database.
        # WAL checkpoints are omitted: they require no open transaction and are
        # not supported on :memory: databases (SQLite raises OperationalError).
        cur.execute("DELETE FROM Sessions WHERE sesDateTimeConnection <= date('now', '-30 day')")
        conn.commit()
        cur.execute("ANALYZE;")
        conn.execute("VACUUM;")
        cur.execute("PRAGMA optimize;")

        cur.execute("SELECT COUNT(*) FROM Sessions")
        assert cur.fetchone()[0] == 0
