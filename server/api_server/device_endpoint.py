#!/usr/bin/env python

import os
import sys
from flask import jsonify, request

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection  # noqa: E402 [flake8 lint suppression]
from helper import is_random_mac, get_setting_value  # noqa: E402 [flake8 lint suppression]
from utils.datetime_utils import timeNowDB, format_date  # noqa: E402 [flake8 lint suppression]
from db.db_helper import row_to_json, get_date_from_period  # noqa: E402 [flake8 lint suppression]

# --------------------------
# Device Endpoints Functions
# --------------------------


def get_device_data(mac):
    """Fetch device info with children, event stats, and presence calculation."""

    # Open temporary connection for this request
    conn = get_temp_db_connection()
    cur = conn.cursor()

    now = timeNowDB()

    # Special case for new device
    if mac.lower() == "new":

        device_data = {
            "devMac": "",
            "devName": "",
            "devOwner": "",
            "devType": "",
            "devVendor": "",
            "devFavorite": 0,
            "devGroup": "",
            "devComments": "",
            "devFirstConnection": now,
            "devLastConnection": now,
            "devLastIP": "",
            "devStaticIP": 0,
            "devScan": 0,
            "devLogEvents": 0,
            "devAlertEvents": 0,
            "devAlertDown": 0,
            "devParentRelType": "default",
            "devReqNicsOnline": 0,
            "devSkipRepeated": 0,
            "devLastNotification": "",
            "devPresentLastScan": 0,
            "devIsNew": 1,
            "devLocation": "",
            "devIsArchived": 0,
            "devParentMAC": "",
            "devParentPort": "",
            "devIcon": "",
            "devGUID": "",
            "devSite": "",
            "devSSID": "",
            "devSyncHubNode": "",
            "devSourcePlugin": "",
            "devCustomProps": "",
            "devStatus": "Unknown",
            "devIsRandomMAC": False,
            "devSessions": 0,
            "devEvents": 0,
            "devDownAlerts": 0,
            "devPresenceHours": 0,
            "devFQDN": "",
        }
        return jsonify(device_data)

    # Compute period date for sessions/events
    period = request.args.get("period", "")  # e.g., '7 days', '1 month', etc.
    period_date_sql = get_date_from_period(period)

    # Fetch device info + computed fields
    sql = f"""
    SELECT
        d.*,
        CASE
            WHEN d.devAlertDown != 0 AND d.devPresentLastScan = 0 THEN 'Down'
            WHEN d.devPresentLastScan = 1 THEN 'On-line'
            ELSE 'Off-line'
        END AS devStatus,

        (SELECT COUNT(*) FROM Sessions
         WHERE ses_MAC = d.devMac AND (
            ses_DateTimeConnection >= {period_date_sql} OR
            ses_DateTimeDisconnection >= {period_date_sql} OR
            ses_StillConnected = 1
         )) AS devSessions,

        (SELECT COUNT(*) FROM Events
         WHERE eve_MAC = d.devMac AND eve_DateTime >= {period_date_sql}
           AND eve_EventType NOT IN ('Connected','Disconnected')) AS devEvents,

        (SELECT COUNT(*) FROM Events
         WHERE eve_MAC = d.devMac AND eve_DateTime >= {period_date_sql}
           AND eve_EventType = 'Device Down') AS devDownAlerts,

        (SELECT CAST(MAX(0, SUM(
            julianday(IFNULL(ses_DateTimeDisconnection,'{now}')) -
            julianday(CASE WHEN ses_DateTimeConnection < {period_date_sql}
                           THEN {period_date_sql} ELSE ses_DateTimeConnection END)
        ) * 24) AS INT)
         FROM Sessions
         WHERE ses_MAC = d.devMac
           AND ses_DateTimeConnection IS NOT NULL
           AND (ses_DateTimeDisconnection IS NOT NULL OR ses_StillConnected = 1)
           AND (ses_DateTimeConnection >= {period_date_sql}
                OR ses_DateTimeDisconnection >= {period_date_sql} OR ses_StillConnected = 1)
        ) AS devPresenceHours

    FROM Devices d
    WHERE d.devMac = ? OR CAST(d.rowid AS TEXT) = ?
    """
    # Fetch device
    cur.execute(sql, (mac, mac))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Device not found"}), 404

    device_data = row_to_json(list(row.keys()), row)
    device_data["devFirstConnection"] = format_date(device_data["devFirstConnection"])
    device_data["devLastConnection"] = format_date(device_data["devLastConnection"])
    device_data["devIsRandomMAC"] = is_random_mac(device_data["devMac"])

    # Fetch children
    cur.execute(
        "SELECT * FROM Devices WHERE devParentMAC = ? ORDER BY devPresentLastScan DESC",
        (device_data["devMac"],),
    )
    children_rows = cur.fetchall()
    children = [row_to_json(list(r.keys()), r) for r in children_rows]
    children_nics = [c for c in children if c.get("devParentRelType") == "nic"]

    device_data["devChildrenDynamic"] = children
    device_data["devChildrenNicsDynamic"] = children_nics

    conn.close()

    return jsonify(device_data)


def set_device_data(mac, data):
    """Update or create a device."""
    if data.get("createNew", False):
        sql = """
        INSERT INTO Devices (
            devMac, devName, devOwner, devType, devVendor, devIcon,
            devFavorite, devGroup, devLocation, devComments,
            devParentMAC, devParentPort, devSSID, devSite,
            devStaticIP, devScan, devAlertEvents, devAlertDown,
            devParentRelType, devReqNicsOnline, devSkipRepeated,
            devIsNew, devIsArchived, devLastConnection,
            devFirstConnection, devLastIP, devGUID, devCustomProps,
            devSourcePlugin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            mac,
            data.get("devName", ""),
            data.get("devOwner", ""),
            data.get("devType", ""),
            data.get("devVendor", ""),
            data.get("devIcon", ""),
            data.get("devFavorite", 0),
            data.get("devGroup", ""),
            data.get("devLocation", ""),
            data.get("devComments", ""),
            data.get("devParentMAC", ""),
            data.get("devParentPort", ""),
            data.get("devSSID", ""),
            data.get("devSite", ""),
            data.get("devStaticIP", 0),
            data.get("devScan", 0),
            data.get("devAlertEvents", 0),
            data.get("devAlertDown", 0),
            data.get("devParentRelType", "default"),
            data.get("devReqNicsOnline", 0),
            data.get("devSkipRepeated", 0),
            data.get("devIsNew", 0),
            data.get("devIsArchived", 0),
            data.get("devLastConnection", timeNowDB()),
            data.get("devFirstConnection", timeNowDB()),
            data.get("devLastIP", ""),
            data.get("devGUID", ""),
            data.get("devCustomProps", ""),
            data.get("devSourcePlugin", "DUMMY"),
        )

    else:
        sql = """
        UPDATE Devices SET
            devName=?, devOwner=?, devType=?, devVendor=?, devIcon=?,
            devFavorite=?, devGroup=?, devLocation=?, devComments=?,
            devParentMAC=?, devParentPort=?, devSSID=?, devSite=?,
            devStaticIP=?, devScan=?, devAlertEvents=?, devAlertDown=?,
            devParentRelType=?, devReqNicsOnline=?, devSkipRepeated=?,
            devIsNew=?, devIsArchived=?, devCustomProps=?
        WHERE devMac=?
        """
        values = (
            data.get("devName", ""),
            data.get("devOwner", ""),
            data.get("devType", ""),
            data.get("devVendor", ""),
            data.get("devIcon", ""),
            data.get("devFavorite", 0),
            data.get("devGroup", ""),
            data.get("devLocation", ""),
            data.get("devComments", ""),
            data.get("devParentMAC", ""),
            data.get("devParentPort", ""),
            data.get("devSSID", ""),
            data.get("devSite", ""),
            data.get("devStaticIP", 0),
            data.get("devScan", 0),
            data.get("devAlertEvents", 0),
            data.get("devAlertDown", 0),
            data.get("devParentRelType", "default"),
            data.get("devReqNicsOnline", 0),
            data.get("devSkipRepeated", 0),
            data.get("devIsNew", 0),
            data.get("devIsArchived", 0),
            data.get("devCustomProps", ""),
            mac,
        )

    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute(sql, values)
    conn.commit()
    conn.close()
    return jsonify({"success": True})


def delete_device(mac):
    """Delete a device by MAC."""
    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Devices WHERE devMac=?", (mac,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


def delete_device_events(mac):
    """Delete all events for a device."""
    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Events WHERE eve_MAC=?", (mac,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


def reset_device_props(mac, data=None):
    """Reset device custom properties to default."""
    default_props = get_setting_value("NEWDEV_devCustomProps")
    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Devices SET devCustomProps=? WHERE devMac=?",
        (default_props, mac),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


def update_device_column(mac, column_name, column_value):
    """
    Update a specific column for a given device.
    Example: update_device_column("AA:BB:CC:DD:EE:FF", "devParentMAC", "Internet")
    """

    conn = get_temp_db_connection()
    cur = conn.cursor()

    # Build safe SQL with column name whitelisted
    sql = f"UPDATE Devices SET {column_name}=? WHERE devMac=?"
    cur.execute(sql, (column_value, mac))
    conn.commit()

    if cur.rowcount > 0:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Device not found"}), 404

    conn.close()

    return jsonify({"success": True})


def copy_device(mac_from, mac_to):
    """
    Copy a device entry from one MAC to another.
    If a device already exists with mac_to, it will be replaced.
    """
    conn = get_temp_db_connection()
    cur = conn.cursor()

    try:
        # Drop temporary table if exists
        cur.execute("DROP TABLE IF EXISTS temp_devices")

        # Create temporary table with source device
        cur.execute(
            "CREATE TABLE temp_devices AS SELECT * FROM Devices WHERE devMac = ?",
            (mac_from,),
        )

        # Update temporary table to target MAC
        cur.execute("UPDATE temp_devices SET devMac = ?", (mac_to,))

        # Delete previous entry with target MAC
        cur.execute("DELETE FROM Devices WHERE devMac = ?", (mac_to,))

        # Insert new entry from temporary table
        cur.execute(
            "INSERT INTO Devices SELECT * FROM temp_devices WHERE devMac = ?", (mac_to,)
        )

        # Drop temporary table
        cur.execute("DROP TABLE temp_devices")

        conn.commit()
        return jsonify(
            {"success": True, "message": f"Device copied from {mac_from} to {mac_to}"}
        )

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)})

    finally:
        conn.close()
