import pytest
import sqlite3


@pytest.fixture
def scan_db():
    """Centralized in-memory SQLite database for all integration tests."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Comprehensive Devices Table
    cur.execute("""
        CREATE TABLE Devices (
            devMac TEXT PRIMARY KEY,
            devLastConnection TEXT,
            devFirstConnection TEXT,
            devPresentLastScan INTEGER DEFAULT 0,
            devForceStatus TEXT,
            devLastIP TEXT,
            devPrimaryIPv4 TEXT,
            devPrimaryIPv6 TEXT,
            devVendor TEXT,
            devParentPort TEXT,
            devParentMAC TEXT,
            devParentRelType TEXT,
            devSite TEXT,
            devSSID TEXT,
            devType TEXT,
            devName TEXT,
            devIcon TEXT,
            devGUID TEXT,
            devSyncHubNode TEXT,
            devOwner TEXT,
            devGroup TEXT,
            devLocation TEXT,
            devComments TEXT,
            devCustomProps TEXT,
            devIsArchived INTEGER DEFAULT 0,
            devIsNew INTEGER DEFAULT 1,
            devFavorite INTEGER DEFAULT 0,
            devScan INTEGER DEFAULT 1,

            -- Authoritative Metadata Columns
            devMacSource TEXT,
            devNameSource TEXT,
            devVendorSource TEXT,
            devLastIPSource TEXT,
            devTypeSource TEXT,
            devSSIDSource TEXT,
            devParentMACSource TEXT,
            devParentPortSource TEXT,
            devParentRelTypeSource TEXT,
            devFQDNSource TEXT,
            devVlanSource TEXT,

            -- Field Locking Columns
            devNameLocked INTEGER DEFAULT 0,
            devTypeLocked INTEGER DEFAULT 0,
            devIconLocked INTEGER DEFAULT 0
        )
    """)

    # 2. CurrentScan Table
    cur.execute("""
        CREATE TABLE CurrentScan (
            scanMac TEXT,
            scanLastIP TEXT,
            scanVendor TEXT,
            scanSourcePlugin TEXT,
            scanName TEXT,
            scanLastQuery TEXT,
            scanLastConnection TEXT,
            scanSyncHubNode TEXT,
            scanSite TEXT,
            scanSSID TEXT,
            scanParentMAC TEXT,
            scanParentPort TEXT,
            scanType TEXT
        )
    """)

    # 3. LatestDeviceScan View (Inner Join for Online Devices)
    cur.execute("""
        CREATE VIEW LatestDeviceScan AS
        WITH RankedScans AS (
            SELECT
                c.*,
                ROW_NUMBER() OVER (
                    PARTITION BY c.scanMac, c.scanSourcePlugin
                    ORDER BY c.scanLastConnection DESC
                ) AS rn
            FROM CurrentScan c
        )
        SELECT d.*, r.* FROM Devices d
        INNER JOIN RankedScans r ON d.devMac = r.scanMac
        WHERE r.rn = 1;
    """)

    conn.commit()
    yield conn
    conn.close()
