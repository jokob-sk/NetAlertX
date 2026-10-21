"""
db_history.py — DevicesHistory table/trigger management.

Creates and maintains:
  - DevicesHistory table + indexes
  - AFTER UPDATE trigger  (trg_devhist_update)
  - AFTER INSERT trigger  (trg_devhist_insert)

Both triggers are driven entirely by two Settings values:
  DEV_HIST_DAYS     — 0 disables the engine entirely (WHEN guard)
  DEV_HIST_TRACKED  — comma-separated list of field names to audit

Attribution uses existing *Source columns where available, falling back
to hard-coded constants for user-only and auto-computed fields.
"""

from logger import mylog

# ---------------------------------------------------------------------------
# Field → changedBy attribution mapping
#
# Each entry: (field_name, changedBy_sql_expression)
#   - Source-tracked fields: read NEW.<field>Source at trigger time
#   - User-only fields:      hard-coded 'user:api'
#   - Auto-computed fields:  hard-coded 'system'
#   - *Source fields:        hard-coded 'system'
# ---------------------------------------------------------------------------
_HIST_FIELDS = [
    # Source-tracked fields (FIELD_SOURCE_MAP)
    ("devMac", "COALESCE(NULLIF(TRIM(NEW.devMacSource), ''), 'system')"),
    ("devName", "COALESCE(NULLIF(TRIM(NEW.devNameSource), ''), 'system')"),
    ("devFQDN", "COALESCE(NULLIF(TRIM(NEW.devFQDNSource), ''), 'system')"),
    ("devLastIP", "COALESCE(NULLIF(TRIM(NEW.devLastIPSource), ''), 'system')"),
    ("devVendor", "COALESCE(NULLIF(TRIM(NEW.devVendorSource), ''), 'system')"),
    ("devSSID", "COALESCE(NULLIF(TRIM(NEW.devSSIDSource), ''), 'system')"),
    ("devParentMAC", "COALESCE(NULLIF(TRIM(NEW.devParentMACSource), ''), 'system')"),
    ("devParentPort", "COALESCE(NULLIF(TRIM(NEW.devParentPortSource), ''), 'system')"),
    ("devParentRelType", "COALESCE(NULLIF(TRIM(NEW.devParentRelTypeSource), ''), 'system')"),
    ("devVlan", "COALESCE(NULLIF(TRIM(NEW.devVlanSource), ''), 'system')"),
    # User-only fields (only setDeviceData() / updateField() touch these)
    ("devOwner", "'user:api'"),
    ("devType", "'user:api'"),
    ("devFavorite", "'user:api'"),
    ("devGroup", "'user:api'"),
    ("devComments", "'user:api'"),
    ("devForceStatus", "'user:api'"),
    ("devStaticIP", "'user:api'"),
    ("devScan", "'user:api'"),
    ("devAlertDown", "'user:api'"),
    ("devCanSleep", "'user:api'"),
    ("devSkipRepeated", "'user:api'"),
    ("devLocation", "'user:api'"),
    ("devIsArchived", "'user:api'"),
    ("devReqNicsOnline", "'user:api'"),
    ("devCustomProps", "'user:api'"),
    # Auto-computed / scan-only fields (no *Source column)
    ("devPrimaryIPv4", "'system'"),
    ("devPrimaryIPv6", "'system'"),
    ("devIcon", "'system'"),
    ("devSite", "'system'"),
    ("devSyncHubNode", "'system'"),
    ("devSourcePlugin", "'system'"),
    # *Source fields themselves
    ("devMacSource", "'system'"),
    ("devNameSource", "'system'"),
    ("devFQDNSource", "'system'"),
    ("devLastIPSource", "'system'"),
    ("devVendorSource", "'system'"),
    ("devSSIDSource", "'system'"),
    ("devParentMACSource", "'system'"),
    ("devParentPortSource", "'system'"),
    ("devParentRelTypeSource", "'system'"),
    ("devVlanSource", "'system'"),
]

# ---------------------------------------------------------------------------
# SQL builders
# ---------------------------------------------------------------------------

_HIST_DAYS_GUARD = (
    "(SELECT CAST(COALESCE(setValue, '0') AS INTEGER) "
    "FROM Settings WHERE setKey = 'DEV_HIST_DAYS') > 0"
)

_TRACKED_CHECK = (
    "instr((SELECT COALESCE(setValue, '') FROM Settings "
    "WHERE setKey = 'DEV_HIST_TRACKED'), '''{field}''') > 0"
)


def _build_update_trigger_sql() -> str:
    """Generate CREATE TRIGGER SQL for AFTER UPDATE on Devices."""
    blocks = []
    for field, attribution in _HIST_FIELDS:
        tracked_check = _TRACKED_CHECK.format(field=field)
        blocks.append(
            f"  INSERT INTO DevicesHistory "
            f"(devGUID, changedColumn, oldValue, newValue, changedBy, timestamp)\n"
            f"  SELECT NEW.devGUID, '{field}', "
            f"CAST(OLD.{field} AS TEXT), CAST(NEW.{field} AS TEXT),\n"
            f"         {attribution},\n"
            f"         datetime('now')\n"
            f"  WHERE (OLD.{field} IS NOT NEW.{field})\n"
            f"    AND COALESCE(NEW.devGUID, '') != ''\n"
            f"    AND {tracked_check};"
        )
    body = "\n".join(blocks)
    return (
        "CREATE TRIGGER trg_devhist_update\n"
        "AFTER UPDATE ON Devices\n"
        "FOR EACH ROW\n"
        f"WHEN {_HIST_DAYS_GUARD}\n"
        "BEGIN\n"
        f"{body}\n"
        "END;"
    )


def _build_insert_trigger_sql() -> str:
    """Generate CREATE TRIGGER SQL for AFTER INSERT on Devices."""
    blocks = []
    for field, attribution in _HIST_FIELDS:
        tracked_check = _TRACKED_CHECK.format(field=field)
        blocks.append(
            f"  INSERT INTO DevicesHistory "
            f"(devGUID, changedColumn, oldValue, newValue, changedBy, timestamp)\n"
            f"  SELECT NEW.devGUID, '{field}', NULL, CAST(NEW.{field} AS TEXT),\n"
            f"         {attribution},\n"
            f"         datetime('now')\n"
            f"  WHERE NEW.{field} IS NOT NULL\n"
            f"    AND COALESCE(NEW.devGUID, '') != ''\n"
            f"    AND {tracked_check};"
        )
    body = "\n".join(blocks)
    return (
        "CREATE TRIGGER trg_devhist_insert\n"
        "AFTER INSERT ON Devices\n"
        "FOR EACH ROW\n"
        f"WHEN {_HIST_DAYS_GUARD}\n"
        "BEGIN\n"
        f"{body}\n"
        "END;"
    )


# ---------------------------------------------------------------------------
# Public ensure_* functions (called from database.py initDB)
# ---------------------------------------------------------------------------

def ensure_deviceshistory_table(sql) -> bool:
    """
    Ensures DevicesHistory table and its indexes exist.

    Also backfills any Devices rows that have NULL/empty devGUID so that
    the history triggers can write records for them.

    Idempotent — uses IF NOT EXISTS throughout.

    Parameters:
        sql: database cursor (must support execute()).
    """
    try:
        sql.execute("""
            CREATE TABLE IF NOT EXISTS DevicesHistory (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                devGUID       TEXT NOT NULL,
                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                changedBy     TEXT NOT NULL,
                changedColumn TEXT NOT NULL,
                oldValue      TEXT,
                newValue      TEXT,
                FOREIGN KEY (devGUID) REFERENCES Devices(devGUID) ON DELETE CASCADE
            )
        """)

        sql.execute(
            "CREATE INDEX IF NOT EXISTS idx_devhist_guid_column "
            "ON DevicesHistory(devGUID, changedColumn)"
        )
        sql.execute(
            "CREATE INDEX IF NOT EXISTS idx_devhist_timestamp "
            "ON DevicesHistory(timestamp)"
        )

        # Backfill any Devices rows that are missing a GUID so the history
        # triggers can record changes for them.
        sql.execute("""
            UPDATE Devices
            SET devGUID = lower(
                hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' ||
                substr(hex(randomblob(2)), 2) || '-' ||
                substr('AB89', 1 + (abs(random()) % 4), 1) ||
                substr(hex(randomblob(2)), 2) || '-' ||
                hex(randomblob(6))
            )
            WHERE devGUID IS NULL OR TRIM(devGUID) = ''
        """)

        mylog("verbose", ["[db_history] DevicesHistory table and indexes ensured"])
        return True
    except Exception as e:
        mylog("none", [f"[db_history] ERROR ensuring DevicesHistory table: {e}"])
        return False


def ensure_deviceshistory_triggers(sql) -> bool:
    """
    Drops and recreates the AFTER UPDATE and AFTER INSERT triggers on Devices.

    Always drops first so that trigger logic is refreshed on every upgrade.

    Parameters:
        sql: database cursor (must support execute()).
    """
    try:
        sql.execute("DROP TRIGGER IF EXISTS trg_devhist_update")
        sql.execute("DROP TRIGGER IF EXISTS trg_devhist_insert")

        update_sql = _build_update_trigger_sql()
        insert_sql = _build_insert_trigger_sql()

        sql.execute(update_sql)
        sql.execute(insert_sql)

        mylog("verbose", ["[db_history] DevicesHistory triggers created"])
        return True
    except Exception as e:
        mylog("none", [f"[db_history] ERROR creating DevicesHistory triggers: {e}"])
        return False
