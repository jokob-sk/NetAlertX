import sys
import pathlib
import sqlite3

sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()) + "/server/")

from scan.device_handling import cleanup_duplicate_devices_by_ip

class DummyDB:
    def __init__(self, conn):
        self.sql_connection = conn
        self.sql = conn.cursor()
    def commitDB(self):
        self.sql_connection.commit()


def create_db(rows):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE Devices (devMac TEXT, devLastIP TEXT, devPresentLastScan INTEGER)"
    )
    for r in rows:
        cur.execute(
            "INSERT INTO Devices (devMac, devLastIP, devPresentLastScan) VALUES (?, ?, ?)",
            r,
        )
    conn.commit()
    return conn


def count_by_ip(cur, ip):
    cur.execute("SELECT COUNT(*) FROM Devices WHERE devLastIP=?", (ip,))
    return cur.fetchone()[0]


def test_cleanup_removes_offline_duplicates():
    rows = [
        ("mac1", "1.2.3.4", 1),
        ("mac2", "1.2.3.4", 0),
        ("mac3", "5.6.7.8", 0),
        ("mac4", "5.6.7.8", 0),
        ("mac5", "9.9.9.9", 1),
        ("mac6", "9.9.9.9", 1),
        ("mac7", "10.0.0.1", 0),
    ]
    conn = create_db(rows)
    db = DummyDB(conn)

    cleanup_duplicate_devices_by_ip(db)

    cur = conn.cursor()
    assert count_by_ip(cur, "1.2.3.4") == 1
    assert count_by_ip(cur, "5.6.7.8") == 1
    assert count_by_ip(cur, "9.9.9.9") == 2
    assert count_by_ip(cur, "10.0.0.1") == 1


def test_cleanup_no_duplicates():
    rows = [
        ("mac1", "1.1.1.1", 1),
        ("mac2", "2.2.2.2", 0),
        ("mac3", "3.3.3.3", 1),
    ]
    conn = create_db(rows)
    db = DummyDB(conn)

    cleanup_duplicate_devices_by_ip(db)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Devices")
    assert cur.fetchone()[0] == 3
