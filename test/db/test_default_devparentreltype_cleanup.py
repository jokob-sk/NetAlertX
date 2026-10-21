"""
Unit tests for the devParentRelType='[]' cleanup migration.

Tests verify that:
- Rows stamped with the literal string '[]' (written before the
  dataType:"array"/default_value:"default" mismatch was fixed in
  newdev_template/config.json) are repaired to 'default'.
- Non-matching values and rows with no match are left untouched.
- The migration is idempotent.
- A SQL failure is caught and reported as False, not raised.
"""

import sys
import os
import pytest
import sqlite3
import tempfile

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from db.db_upgrade import cleanup_existing_default_devParentRelType  # noqa: E402


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE Devices (
            devMac TEXT PRIMARY KEY COLLATE NOCASE,
            devParentRelType TEXT
        )
    """)

    conn.commit()

    yield cursor, conn

    conn.close()
    os.unlink(db_path)


class TestCleanupExistingDefaultDevParentRelType:
    """Test suite for the one-time/idempotent data repair migration"""

    def test_cleanup_fixes_matching_rows(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentRelType) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:01", "[]"),
        )
        conn.commit()

        assert cleanup_existing_default_devParentRelType(cursor) is True

        cursor.execute(
            "SELECT devParentRelType FROM Devices WHERE devMac = ?",
            ("aa:bb:cc:dd:ee:01",),
        )
        assert cursor.fetchone() == ("default",)

    def test_cleanup_preserves_nonmatching_values(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentRelType) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:02", "nic"),
        )
        conn.commit()

        cleanup_existing_default_devParentRelType(cursor)

        cursor.execute(
            "SELECT devParentRelType FROM Devices WHERE devMac = ?",
            ("aa:bb:cc:dd:ee:02",),
        )
        assert cursor.fetchone() == ("nic",)

    def test_cleanup_no_matching_rows_is_a_noop(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentRelType) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:03", "default"),
        )
        conn.commit()

        assert cleanup_existing_default_devParentRelType(cursor) is True

        cursor.execute(
            "SELECT devParentRelType FROM Devices WHERE devMac = ?",
            ("aa:bb:cc:dd:ee:03",),
        )
        assert cursor.fetchone() == ("default",)

    def test_cleanup_is_idempotent(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentRelType) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:04", "[]"),
        )
        conn.commit()

        assert cleanup_existing_default_devParentRelType(cursor) is True
        assert cleanup_existing_default_devParentRelType(cursor) is True

        cursor.execute(
            "SELECT devParentRelType FROM Devices WHERE devMac = ?",
            ("aa:bb:cc:dd:ee:04",),
        )
        assert cursor.fetchone() == ("default",)

    def test_cleanup_reports_sql_failure_as_false(self):
        """No devParentRelType column at all -> the UPDATE raises, caught and
        reported as False rather than propagating the exception."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE Devices (devMac TEXT PRIMARY KEY)")
        conn.commit()

        try:
            assert cleanup_existing_default_devParentRelType(cursor) is False
        finally:
            conn.close()
            os.unlink(db_path)
