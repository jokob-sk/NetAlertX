# ---------------------------------------------------------------------------------#
#  NetAlertX                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #
#                                                                                 #
#  reporting.py - NetAlertX Back module. Template to email reporting in HTML format #
# ---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
# ---------------------------------------------------------------------------------#

import json
import os
import sys

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from helper import (  # noqa: E402 [flake8 lint suppression]
    get_setting_value,
)
from logger import mylog  # noqa: E402 [flake8 lint suppression]
from db.sql_safe_builder import create_safe_condition_builder  # noqa: E402 [flake8 lint suppression]
from utils.datetime_utils import get_timezone_offset  # noqa: E402 [flake8 lint suppression]

# ===============================================================================
# REPORTING
# ===============================================================================


# -------------------------------------------------------------------------------
def get_notifications(db):
    sql = db.sql  # TO-DO

    # Reporting section
    mylog("verbose", ["[Notification] Check if something to report"])

    # prepare variables for JSON construction
    json_new_devices = []
    json_new_devices_meta = {}
    json_down_devices = []
    json_down_devices_meta = {}
    json_down_reconnected = []
    json_down_reconnected_meta = {}
    json_events = []
    json_events_meta = {}
    json_plugins = []
    json_plugins_meta = {}

    # Disable reporting on events for devices where reporting is disabled based on the MAC address

    # Disable notifications (except down/down reconnected) on devices where devAlertEvents is disabled
    sql.execute("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType not in ('Device Down', 'Down Reconnected', 'New Device' ) AND eve_MAC IN
                        (
                            SELECT devMac FROM Devices WHERE devAlertEvents = 0
                        )""")

    # Disable down/down reconnected notifications on devices where devAlertDown is disabled
    sql.execute("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType in ('Device Down', 'Down Reconnected') AND eve_MAC IN
                        (
                            SELECT devMac FROM Devices WHERE devAlertDown = 0
                        )""")

    sections = get_setting_value("NTFPRCS_INCLUDED_SECTIONS")

    mylog("verbose", ["[Notification] Included sections: ", sections])

    if "new_devices" in sections:
        # Compose New Devices Section (no empty lines in SQL queries!)
        # Use SafeConditionBuilder to prevent SQL injection vulnerabilities
        condition_builder = create_safe_condition_builder()
        new_dev_condition_setting = get_setting_value("NTFPRCS_new_dev_condition")

        try:
            safe_condition, parameters = condition_builder.get_safe_condition_legacy(
                new_dev_condition_setting
            )
            sqlQuery = """SELECT
                            eve_MAC as MAC,
                            eve_DateTime as Datetime,
                            devLastIP as IP,
                            eve_EventType as "Event Type",
                            devName as "Device name",
                            devComments as Comments FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                            AND eve_EventType = 'New Device' {}
                        ORDER BY eve_DateTime""".format(safe_condition)
        except (ValueError, KeyError, TypeError) as e:
            mylog("verbose", ["[Notification] Error building safe condition for new devices: ", e])
            # Fall back to safe default (no additional conditions)
            sqlQuery = """SELECT
                            eve_MAC as MAC,
                            eve_DateTime as Datetime,
                            devLastIP as IP,
                            eve_EventType as "Event Type",
                            devName as "Device name",
                            devComments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                            AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime"""
            parameters = {}

        mylog("debug", ["[Notification] new_devices SQL query: ", sqlQuery])
        mylog("debug", ["[Notification] new_devices parameters: ", parameters])

        # Get the events as JSON using parameterized query
        json_obj = db.get_table_as_json(sqlQuery, parameters)

        json_new_devices_meta = {
            "title": "🆕 New devices",
            "columnNames": json_obj.columnNames,
        }

        json_new_devices = json_obj.json["data"]

    if "down_devices" in sections:
        # Compose Devices Down Section
        # - select only Down Alerts with pending email of devices that didn't reconnect within the specified time window
        minutes = int(get_setting_value("NTFPRCS_alert_down_time") or 0)
        tz_offset = get_timezone_offset()
        sqlQuery = f"""
                    SELECT devName, eve_MAC, devVendor, eve_IP, eve_DateTime, eve_EventType
                        FROM Events_Devices AS down_events
                        WHERE eve_PendingAlertEmail = 1
                        AND down_events.eve_EventType = 'Device Down'
                        AND eve_DateTime < datetime('now', '-{minutes} minutes', '{tz_offset}')
                        AND NOT EXISTS (
                            SELECT 1
                            FROM Events AS connected_events
                            WHERE connected_events.eve_MAC = down_events.eve_MAC
                                AND connected_events.eve_EventType = 'Connected'
                                AND connected_events.eve_DateTime > down_events.eve_DateTime
                        )
                        ORDER BY down_events.eve_DateTime;
                    """

        # Get the events as JSON
        json_obj = db.get_table_as_json(sqlQuery)

        json_down_devices_meta = {
            "title": "🔴 Down devices",
            "columnNames": json_obj.columnNames,
        }
        json_down_devices = json_obj.json["data"]

        mylog("debug", f"[Notification] json_down_devices: {json.dumps(json_down_devices)}")

    if "down_reconnected" in sections:
        # Compose Reconnected Down Section
        # - select only Devices, that were previously down and now are Connected
        sqlQuery = """
                        SELECT devName, eve_MAC, devVendor, eve_IP, eve_DateTime, eve_EventType
                        FROM Events_Devices AS reconnected_devices
                            WHERE reconnected_devices.eve_EventType = 'Down Reconnected'
                            AND reconnected_devices.eve_PendingAlertEmail = 1
                        ORDER BY reconnected_devices.eve_DateTime;
                    """

        # Get the events as JSON
        json_obj = db.get_table_as_json(sqlQuery)

        json_down_reconnected_meta = {
            "title": "🔁 Reconnected down devices",
            "columnNames": json_obj.columnNames,
        }
        json_down_reconnected = json_obj.json["data"]

        mylog("debug", f"[Notification] json_down_reconnected: {json.dumps(json_down_reconnected)}")

    if "events" in sections:
        # Compose Events Section (no empty lines in SQL queries!)
        # Use SafeConditionBuilder to prevent SQL injection vulnerabilities
        condition_builder = create_safe_condition_builder()
        event_condition_setting = get_setting_value("NTFPRCS_event_condition")

        try:
            safe_condition, parameters = condition_builder.get_safe_condition_legacy(
                event_condition_setting
            )
            sqlQuery = """SELECT
                            eve_MAC as MAC,
                            eve_DateTime as Datetime,
                            devLastIP as IP,
                            eve_EventType as "Event Type",
                            devName as "Device name",
                            devComments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                            AND eve_EventType IN ('Connected', 'Down Reconnected', 'Disconnected','IP Changed') {}
                        ORDER BY eve_DateTime""".format(safe_condition)
        except Exception as e:
            mylog("verbose", f"[Notification] Error building safe condition for events: {e}")
            # Fall back to safe default (no additional conditions)
            sqlQuery = """SELECT
                            eve_MAC as MAC,
                            eve_DateTime as Datetime,
                            devLastIP as IP,
                            eve_EventType as "Event Type",
                            devName as "Device name",
                            devComments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                            AND eve_EventType IN ('Connected', 'Down Reconnected', 'Disconnected','IP Changed')
                        ORDER BY eve_DateTime"""
            parameters = {}

        mylog("debug", ["[Notification] events SQL query: ", sqlQuery])
        mylog("debug", ["[Notification] events parameters: ", parameters])

        # Get the events as JSON using parameterized query
        json_obj = db.get_table_as_json(sqlQuery, parameters)

        json_events_meta = {"title": "⚡ Events", "columnNames": json_obj.columnNames}
        json_events = json_obj.json["data"]

    if "plugins" in sections:
        # Compose Plugins Section
        sqlQuery = """SELECT
                        Plugin,
                        Object_PrimaryId,
                        Object_SecondaryId,
                        DateTimeChanged,
                        Watched_Value1,
                        Watched_Value2,
                        Watched_Value3,
                        Watched_Value4,
                        Status
                    from Plugins_Events"""

        # Get the events as JSON
        json_obj = db.get_table_as_json(sqlQuery)

        json_plugins_meta = {"title": "🔌 Plugins", "columnNames": json_obj.columnNames}
        json_plugins = json_obj.json["data"]

    final_json = {
        "new_devices": json_new_devices,
        "new_devices_meta": json_new_devices_meta,
        "down_devices": json_down_devices,
        "down_devices_meta": json_down_devices_meta,
        "down_reconnected": json_down_reconnected,
        "down_reconnected_meta": json_down_reconnected_meta,
        "events": json_events,
        "events_meta": json_events_meta,
        "plugins": json_plugins,
        "plugins_meta": json_plugins_meta,
    }

    return final_json


# -------------------------------------------------------------------------------
def skip_repeated_notifications(db):
    """
    Skips sending alerts for devices recently notified.

    Clears `eve_PendingAlertEmail` for events linked to devices whose last
    notification time is within their `devSkipRepeated` interval.

    Args:
        db: Database object with `.sql.execute()` and `.commitDB()`.
    """

    # Skip repeated notifications
    # due strfime : Overflow --> use  "strftime / 60"
    mylog("verbose", "[Skip Repeated Notifications] Skip Repeated")

    db.sql.execute("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_MAC IN
                        (
                        SELECT devMac FROM Devices
                        WHERE devLastNotification IS NOT NULL
                          AND devLastNotification <>""
                          AND (strftime("%s", devLastNotification)/60 +
                                devSkipRepeated * 60) >
                              (strftime('%s','now','localtime')/60 )
                        )
                 """)

    db.commitDB()
