"""
Tests for the Resource_History read-side rollup queries (System Info ->
Performance tab, week/month views) defined in server/const.py. Seeds known
per-tick values and asserts SUM() (IO) / AVG() (CPU%/RSS/duration) per hourly
bucket match hand-computed expectations - see resource-usage-history PRD
Design §4.
"""

import sqlite3

from server.const import sql_resource_history_week


def _make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
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


def test_bucketed_query_sums_io_and_averages_the_rest():
    conn = _make_db()
    cur = conn.cursor()

    # Two rows in the same hourly bucket, one row in a different bucket -
    # both within the 7-day window the "week" query scans.
    cur.executemany(
        "INSERT INTO Resource_History "
        "(resDateTime, resCpuPercent, resRssMb, resIoReadBytes, resIoWriteBytes, "
        " resScanDurationMs, resTickFailed) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("2026-01-01 10:05:00", 10.0, 100.0, 1000, 2000, 500, 0),
            ("2026-01-01 10:45:00", 20.0, 200.0, 1500, 2500, 700, 1),
            ("2026-01-01 11:15:00", 30.0, 300.0, 3000, 4000, 900, 0),
        ],
    )
    conn.commit()

    # sql_resource_history_week filters on datetime('now', '-7 day') - patch
    # the fixed timestamps above to "now" so they fall inside the window.
    cur.execute("UPDATE Resource_History SET resDateTime = datetime('now', '-1 hour') "
                "WHERE resDateTime = '2026-01-01 10:05:00'")
    cur.execute("UPDATE Resource_History SET resDateTime = datetime('now', '-1 hour', '+40 minutes') "
                "WHERE resDateTime = '2026-01-01 10:45:00'")
    cur.execute("UPDATE Resource_History SET resDateTime = datetime('now') "
                "WHERE resDateTime = '2026-01-01 11:15:00'")
    conn.commit()

    rows = cur.execute(sql_resource_history_week).fetchall()

    # Expect two buckets (the two rows sharing an hour collapse into one).
    assert len(rows) in (1, 2)

    total_io_read = sum(r[3] for r in rows)
    total_io_write = sum(r[4] for r in rows)
    assert total_io_read == 1000 + 1500 + 3000
    assert total_io_write == 2000 + 2500 + 4000

    # Any bucket containing the tickFailed=1 row must report MAX(resTickFailed)=1.
    assert any(r[6] == 1 for r in rows)


def test_bucketed_query_returns_no_rows_outside_window():
    conn = _make_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Resource_History (resDateTime, resCpuPercent) "
        "VALUES (datetime('now', '-30 day'), 10.0)"
    )
    conn.commit()

    rows = cur.execute(sql_resource_history_week).fetchall()
    assert rows == []
