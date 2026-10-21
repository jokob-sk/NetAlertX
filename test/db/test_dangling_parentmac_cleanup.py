"""
Unit tests for dangling devParentMAC cleanup.

Tests verify that:
- Deleting a device clears devParentMAC/devParentMACSource on devices that
  referenced it as their Parent Node.
- Sentinel values ('', 'internet', 'null') are never touched.
- Valid parent references are left untouched.
- The one-time migration repairs pre-existing dangling data and is idempotent.

Note: the NEWDEV_devParentMAC *setting* is intentionally NOT handled here.
Settings are sourced from app.conf and get re-imported verbatim on every
restart, so a DB-only fix would be silently reverted. That case is instead
guarded against at the point of use in create_new_devices() — see
test/scan/test_field_lock_scan_integration.py.
"""

import sys
import os
import pytest
import sqlite3
import tempfile

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from db.db_upgrade import (  # noqa: E402
    ensure_dangling_parentmac_cleanup_trigger,
    cleanup_existing_dangling_parentmac,
)


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
            devParentMAC TEXT,
            devParentMACSource TEXT
        )
    """)

    conn.commit()

    yield cursor, conn

    conn.close()
    os.unlink(db_path)


class TestDanglingParentMacTrigger:
    """Test suite for the AFTER DELETE cleanup trigger"""

    def test_trigger_clears_dependent_devices_on_delete(self, temp_db):
        cursor, conn = temp_db
        assert ensure_dangling_parentmac_cleanup_trigger(cursor) is True

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC, devParentMACSource) VALUES (?, ?, ?)",
            ("aa:bb:cc:dd:ee:01", "", ""),
        )
        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC, devParentMACSource) VALUES (?, ?, ?)",
            ("aa:bb:cc:dd:ee:02", "aa:bb:cc:dd:ee:01", "NEWDEV"),
        )
        conn.commit()

        cursor.execute("DELETE FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:01",))
        conn.commit()

        cursor.execute(
            "SELECT devParentMAC, devParentMACSource FROM Devices WHERE devMac = ?",
            ("aa:bb:cc:dd:ee:02",),
        )
        row = cursor.fetchone()
        assert row == ("", "")

    def test_trigger_ignores_unrelated_deletes(self, temp_db):
        cursor, conn = temp_db
        ensure_dangling_parentmac_cleanup_trigger(cursor)

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:01", "internet"),
        )
        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:02", ""),
        )
        conn.commit()

        cursor.execute("DELETE FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:02",))
        conn.commit()

        cursor.execute(
            "SELECT devParentMAC FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:01",)
        )
        assert cursor.fetchone() == ("internet",)


class TestCleanupExistingDanglingParentMac:
    """Test suite for the one-time/idempotent data repair migration"""

    def test_cleanup_clears_dangling_reference(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC, devParentMACSource) VALUES (?, ?, ?)",
            ("aa:bb:cc:dd:ee:02", "aa:bb:cc:dd:ee:99", "NEWDEV"),
        )
        conn.commit()

        assert cleanup_existing_dangling_parentmac(cursor) is True

        cursor.execute(
            "SELECT devParentMAC, devParentMACSource FROM Devices WHERE devMac = ?",
            ("aa:bb:cc:dd:ee:02",),
        )
        assert cursor.fetchone() == ("", "")

    def test_cleanup_preserves_valid_and_sentinel_values(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:01", ""),
        )
        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:02", "aa:bb:cc:dd:ee:01"),
        )
        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:03", "internet"),
        )
        conn.commit()

        cleanup_existing_dangling_parentmac(cursor)

        cursor.execute(
            "SELECT devParentMAC FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:02",)
        )
        assert cursor.fetchone() == ("aa:bb:cc:dd:ee:01",)

        cursor.execute(
            "SELECT devParentMAC FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:03",)
        )
        assert cursor.fetchone() == ("internet",)

    def test_cleanup_is_idempotent(self, temp_db):
        cursor, conn = temp_db

        cursor.execute(
            "INSERT INTO Devices (devMac, devParentMAC) VALUES (?, ?)",
            ("aa:bb:cc:dd:ee:02", "aa:bb:cc:dd:ee:99"),
        )
        conn.commit()

        assert cleanup_existing_dangling_parentmac(cursor) is True
        assert cleanup_existing_dangling_parentmac(cursor) is True

        cursor.execute(
            "SELECT devParentMAC FROM Devices WHERE devMac = ?", ("aa:bb:cc:dd:ee:02",)
        )
        assert cursor.fetchone() == ("",)
