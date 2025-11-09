#!/usr/bin/env python

import os
import sys
from datetime import datetime
from flask import jsonify

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection
from helper import is_random_mac, mylog
from db.db_helper import row_to_json, get_date_from_period
from utils.datetime_utils import format_date, format_date_iso, format_event_date, ensure_datetime


# --------------------------
# Events Endpoints Functions
# --------------------------


def create_event(
    mac: str,
    ip: str,
    event_type: str = "Device Down",
    additional_info: str = "",
    pending_alert: int = 1,
    event_time: datetime | None = None,
):
    """
    Insert a single event into the Events table and return a standardized JSON response.
    Exceptions will propagate to the caller.
    """
    conn = get_temp_db_connection()
    cur = conn.cursor()
    if isinstance(event_time, str):
        start_time = ensure_datetime(event_time)

    start_time = ensure_datetime(event_time)

    cur.execute(
        """
        INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime, eve_EventType, eve_AdditionalInfo, eve_PendingAlertEmail)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (mac, ip, start_time, event_type, additional_info, pending_alert),
    )

    conn.commit()
    conn.close()

    mylog("debug", f"[Events] Created event for {mac} ({event_type})")
    return jsonify({"success": True, "message": f"Created event for {mac}"})


def get_events(mac=None):
    """
    Fetch all events, or events for a specific MAC if provided.
    Returns JSON list of events.
    """
    conn = get_temp_db_connection()
    cur = conn.cursor()

    if mac:
        sql = "SELECT * FROM Events WHERE eve_MAC=? ORDER BY eve_DateTime DESC"
        cur.execute(sql, (mac,))
    else:
        sql = "SELECT * FROM Events ORDER BY eve_DateTime DESC"
        cur.execute(sql)

    rows = cur.fetchall()
    events = [row_to_json(list(r.keys()), r) for r in rows]

    conn.close()
    return jsonify({"success": True, "events": events})


def delete_events_older_than(days):
    """Delete all events older than a specified number of days"""

    conn = get_temp_db_connection()
    cur = conn.cursor()

    # Use a parameterized query with sqlite date function
    sql = "DELETE FROM Events WHERE eve_DateTime <= date('now', ?)"
    cur.execute(sql, [f"-{days} days"])

    conn.commit()
    conn.close()

    return jsonify(
        {"success": True, "message": f"Deleted events older than {days} days"}
    )


def delete_events():
    """Delete all events"""

    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = "DELETE FROM Events"
    cur.execute(sql)
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Deleted all events"})


def get_events_totals(period: str = "7 days"):
    """
    Return counts for events and sessions totals over a given period.
    period: "7 days", "1 month", "1 year", "100 years"
    """
    # Convert period to SQLite date expression
    period_date_sql = get_date_from_period(period)

    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = f"""
        SELECT 
            (SELECT COUNT(*) FROM Events WHERE eve_DateTime >= {period_date_sql}) AS all_events,
            (SELECT COUNT(*) FROM Sessions WHERE 
                ses_DateTimeConnection >= {period_date_sql}
                OR ses_DateTimeDisconnection >= {period_date_sql}
                OR ses_StillConnected = 1
            ) AS sessions,
            (SELECT COUNT(*) FROM Sessions WHERE 
                (ses_DateTimeConnection IS NULL AND ses_DateTimeDisconnection >= {period_date_sql})
                OR (ses_DateTimeDisconnection IS NULL AND ses_StillConnected = 0 AND ses_DateTimeConnection >= {period_date_sql})
            ) AS missing,
            (SELECT COUNT(*) FROM Events WHERE eve_DateTime >= {period_date_sql} AND eve_EventType LIKE 'VOIDED%') AS voided,
            (SELECT COUNT(*) FROM Events WHERE eve_DateTime >= {period_date_sql} AND eve_EventType LIKE 'New Device') AS new,
            (SELECT COUNT(*) FROM Events WHERE eve_DateTime >= {period_date_sql} AND eve_EventType LIKE 'Device Down') AS down
    """

    cur.execute(sql)
    row = cur.fetchone()
    conn.close()

    # Return as JSON array
    result_json = [row[0], row[1], row[2], row[3], row[4], row[5]]
    return jsonify(result_json)
