# -------------------------------------------------------------------------------
# notification_sections.py — Single source of truth for notification section
# metadata: titles, SQL templates, datetime fields, and section ordering.
#
# Both reporting.py and notification_instance.py import from here.
# -------------------------------------------------------------------------------

# Canonical processing order
SECTION_ORDER = [
    "new_devices",
    "down_devices",
    "down_reconnected",
    "events",
    "plugins",
]

# Section display titles (used in text + HTML notifications)
SECTION_TITLES = {
    "new_devices": "🆕 New devices",
    "down_devices": "🔴 Down devices",
    "down_reconnected": "🔁 Reconnected down devices",
    "events": "⚡ Events",
    "plugins": "🔌 Plugins",
}

# Which column(s) contain datetime values per section (for timezone conversion)
DATETIME_FIELDS = {
    "new_devices": ["eveDateTime"],
    "down_devices": ["eveDateTime"],
    "down_reconnected": ["eveDateTime"],
    "events": ["eveDateTime"],
    "plugins": ["dateTimeChanged"],
}

# ---------------------------------------------------------------------------
# SQL templates
#
# All device sections use unified DB column names so the JSON output
# has consistent field names across new_devices, down_devices,
# down_reconnected, and events.
#
# Placeholders:
#   {condition}          — optional WHERE clause appended by condition builder
#   {alert_down_minutes} — runtime value, only used by down_devices
#
# Every section here reads through Events_Devices, which LEFT JOINs Devices
# onto Events - a device's pending event survives deleting the device (Events
# is kept as a persistent audit trail, not cleaned up on delete), so the join
# still returns that row with every Devices-sourced column NULL. The
# `devMac IS NOT NULL` guard in each template below is what excludes that
# orphaned row from notifications; it does not affect the underlying Events
# row itself, which the events.php page still shows.
# ---------------------------------------------------------------------------
SQL_TEMPLATES = {
    "new_devices": """
        SELECT
            devName,
            eveMac,
            devVendor,
            devLastIP as eveIp,
            eveDateTime,
            eveEventType,
            devComments,
            devVlan,
            devSite,
            devSSID
        FROM Events_Devices
        WHERE evePendingAlertEmail = 1
          AND eveEventType = 'New Device' {condition}
          AND devMac IS NOT NULL
        ORDER BY eveDateTime
    """,
    "down_devices": """
        SELECT
            devName,
            eveMac,
            devVendor,
            eveIp,
            eveDateTime,
            eveEventType,
            devComments,
            devVlan,
            devSite,
            devSSID
        FROM Events_Devices AS down_events
        WHERE evePendingAlertEmail = 1
          AND down_events.eveEventType = 'Device Down'
          AND eveDateTime < datetime('now', '-{alert_down_minutes} minutes')
          AND down_events.devMac IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM Events AS connected_events
              WHERE connected_events.eveMac = down_events.eveMac
                AND connected_events.eveEventType = 'Connected'
                AND connected_events.eveDateTime > down_events.eveDateTime
          )
        ORDER BY down_events.eveDateTime
    """,
    "down_reconnected": """
        SELECT
            devName,
            reconnected_devices.eveMac,
            devVendor,
            reconnected_devices.eveIp,
            reconnected_devices.eveDateTime,
            reconnected_devices.eveEventType,
            devComments,
            devVlan,
            devSite,
            devSSID
        FROM Events_Devices AS reconnected_devices
        WHERE reconnected_devices.eveEventType = 'Down Reconnected'
          AND reconnected_devices.evePendingAlertEmail = 1
          AND reconnected_devices.devMac IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM Events AS newer
              WHERE newer.eveMac = reconnected_devices.eveMac
                AND newer.eveEventType = 'Down Reconnected'
                AND newer.evePendingAlertEmail = 1
                AND newer.eveDateTime > reconnected_devices.eveDateTime
          )
        ORDER BY reconnected_devices.eveDateTime
    """,
    "events": """
        SELECT
            devName,
            eveMac,
            devVendor,
            devLastIP as eveIp,
            eveDateTime,
            eveEventType,
            devComments,
            devVlan,
            devSite,
            devSSID
        FROM Events_Devices
        WHERE evePendingAlertEmail = 1
          AND eveEventType IN ({event_types}) {condition}
          AND devMac IS NOT NULL
        ORDER BY eveDateTime
    """,
    "plugins": """
        SELECT
            plugin,
            objectPrimaryId,
            objectSecondaryId,
            dateTimeChanged,
            watchedValue1,
            watchedValue2,
            watchedValue3,
            watchedValue4,
            status
        FROM Plugins_Events
    """,
}

# Sections that support user-defined condition filters
SECTIONS_WITH_CONDITIONS = {"new_devices", "events"}

# Legacy setting key mapping for condition filters
SECTION_CONDITION_MAP = {
    "new_devices": "NTFPRCS_new_dev_condition",
    "events": "NTFPRCS_event_condition",
}
