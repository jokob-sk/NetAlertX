"""
Single source of truth for the Events/Sessions/AppEvents/Notifications column
lists - used by both the runtime backfill loop (db_upgrade.ensure_table_columns())
and the CI drift-check test (test/db/test_schema_drift_guard.py) against
server/db/schema/app.sql, per scan-pipeline-hardening.md Design §3.

Unlike Devices (server/database.py's ~18 ensure_column() calls, unrelated to
this file), Events/Sessions/Notifications have no drop/recreate safety net
and previously had zero ensure_column() calls at all - app.sql was the only
definition of their schema, with nothing to catch it drifting from what the
rest of the code expects. This is additive/detection-and-backfill only; it
doesn't change any column's meaning or add new columns beyond what app.sql
already defines today.

AppEvents is included here too (for the drift-check test's benefit, since
app.sql also defines it and workflows/app_events.py's inline CREATE TABLE is
a second definition worth keeping in sync), but is NOT part of the runtime
backfill loop in database.py's initDB() - AppEvent_obj.__init__() already
unconditionally drops and recreates the table on every startup, making its
drift harmless the same way ensure_CurrentScan() does for CurrentScan. Found
this while implementing the backfill loop, not before - the correction is
recorded in scan-pipeline-hardening.md.

Column types are copied verbatim from server/db/schema/app.sql's CREATE
TABLE statements for these four tables - keep in sync if that file changes,
the drift-check test will fail loudly if it doesn't.
"""

EVENTS_COLUMNS = {
    "eveMac": "STRING (50)",
    "eveIp": "STRING (50)",
    "eveDateTime": "DATETIME",
    "eveEventType": "STRING (30)",
    "eveAdditionalInfo": "STRING (250)",
    "evePendingAlertEmail": "BOOLEAN",
    "evePairEventRowid": "INTEGER",
}

SESSIONS_COLUMNS = {
    "sesMac": "STRING (50)",
    "sesIp": "STRING (50)",
    "sesEventTypeConnection": "STRING (30)",
    "sesDateTimeConnection": "DATETIME",
    "sesEventTypeDisconnection": "STRING (30)",
    "sesDateTimeDisconnection": "DATETIME",
    "sesStillConnected": "BOOLEAN",
    "sesAdditionalInfo": "STRING (250)",
}

APPEVENTS_COLUMNS = {
    "index": "INTEGER",
    "guid": "TEXT",
    "appEventProcessed": "BOOLEAN",
    "dateTimeCreated": "TEXT",
    "objectType": "TEXT",
    "objectGuid": "TEXT",
    "objectPlugin": "TEXT",
    "objectPrimaryId": "TEXT",
    "objectSecondaryId": "TEXT",
    "objectForeignKey": "TEXT",
    "objectIndex": "TEXT",
    "objectIsNew": "BOOLEAN",
    "objectIsArchived": "BOOLEAN",
    "objectStatusColumn": "TEXT",
    "objectStatus": "TEXT",
    "appEventType": "TEXT",
    "helper1": "TEXT",
    "helper2": "TEXT",
    "helper3": "TEXT",
    "extra": "TEXT",
}

NOTIFICATIONS_COLUMNS = {
    "index": "INTEGER",
    "guid": "TEXT",
    "dateTimeCreated": "TEXT",
    "dateTimePushed": "TEXT",
    "status": "TEXT",
    "json": "TEXT",
    "text": "TEXT",
    "html": "TEXT",
    "publishedVia": "TEXT",
    "extra": "TEXT",
}

# Table name -> {column_name: sql_type}. Drives both the backfill loop and
# the drift-detection test - the one place these four tables' expected
# column lists are written down in Python.
TABLE_COLUMNS = {
    "Events": EVENTS_COLUMNS,
    "Sessions": SESSIONS_COLUMNS,
    "AppEvents": APPEVENTS_COLUMNS,
    "Notifications": NOTIFICATIONS_COLUMNS,
}
