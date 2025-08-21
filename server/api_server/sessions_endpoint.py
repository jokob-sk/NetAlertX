#!/usr/bin/env python

import json
import subprocess
import argparse
import os
import pathlib
import sys
from datetime import datetime
from flask import jsonify, request

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection
from helper import is_random_mac, format_date, get_setting_value, format_date_iso, format_event_date, mylog, timeNowTZ
from db.db_helper import row_to_json


# --------------------------
# Sessions Endpoints Functions
# --------------------------
# -------------------------------------------------------------------------------------------
def create_session(mac, ip, start_time, end_time=None, event_type_conn="Connected", event_type_disc="Disconnected"):
    """Insert a new session into Sessions table"""
    conn = get_temp_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Sessions (ses_MAC, ses_IP, ses_DateTimeConnection, ses_DateTimeDisconnection, 
                              ses_EventTypeConnection, ses_EventTypeDisconnection)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mac, ip, start_time, end_time, event_type_conn, event_type_disc))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Session created for MAC {mac}"})


# -------------------------------------------------------------------------------------------
def delete_session(mac):
    """Delete all sessions for a given MAC"""
    conn = get_temp_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM Sessions WHERE ses_MAC = ?", (mac,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Deleted sessions for MAC {mac}"})


# -------------------------------------------------------------------------------------------
def get_sessions(mac=None, start_date=None, end_date=None):
    """Retrieve sessions optionally filtered by MAC and date range"""
    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = "SELECT * FROM Sessions WHERE 1=1"
    params = []

    if mac:
        sql += " AND ses_MAC = ?"
        params.append(mac)
    if start_date:
        sql += " AND ses_DateTimeConnection >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND ses_DateTimeDisconnection <= ?"
        params.append(end_date)

    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    conn.close()

    # Convert rows to list of dicts
    table_data = [dict(r) for r in rows]

    return jsonify({"success": True, "sessions": table_data})



def get_sessions_calendar(start_date, end_date):
    """
    Fetch sessions between a start and end date for calendar display.
    Returns JSON list of calendar sessions.
    """

    if not start_date or not end_date:
        return jsonify({"success": False, "error": "Missing start or end date"}), 400

    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = """
        -- Correct missing connection/disconnection sessions:
        -- If ses_EventTypeConnection is missing, backfill from last disconnection
        -- If ses_EventTypeDisconnection is missing, forward-fill from next connection

        SELECT 
            SES1.ses_MAC, SES1.ses_EventTypeConnection, SES1.ses_DateTimeConnection,
            SES1.ses_EventTypeDisconnection, SES1.ses_DateTimeDisconnection, SES1.ses_IP,
            SES1.ses_AdditionalInfo, SES1.ses_StillConnected,

            CASE
              WHEN SES1.ses_EventTypeConnection = '<missing event>' THEN
                IFNULL(
                  (SELECT MAX(SES2.ses_DateTimeDisconnection) 
                   FROM Sessions AS SES2 
                   WHERE SES2.ses_MAC = SES1.ses_MAC 
                     AND SES2.ses_DateTimeDisconnection < SES1.ses_DateTimeDisconnection
                     AND SES2.ses_DateTimeDisconnection BETWEEN Date(?) AND Date(?)
                  ),
                  DATETIME(SES1.ses_DateTimeDisconnection, '-1 hour')
                )
              ELSE SES1.ses_DateTimeConnection
            END AS ses_DateTimeConnectionCorrected,

            CASE
              WHEN SES1.ses_EventTypeDisconnection = '<missing event>' THEN
                (SELECT MIN(SES2.ses_DateTimeConnection) 
                 FROM Sessions AS SES2 
                 WHERE SES2.ses_MAC = SES1.ses_MAC 
                   AND SES2.ses_DateTimeConnection > SES1.ses_DateTimeConnection
                   AND SES2.ses_DateTimeConnection BETWEEN Date(?) AND Date(?)
                )
              ELSE SES1.ses_DateTimeDisconnection
            END AS ses_DateTimeDisconnectionCorrected

        FROM Sessions AS SES1
        WHERE (SES1.ses_DateTimeConnection BETWEEN Date(?) AND Date(?))
           OR (SES1.ses_DateTimeDisconnection BETWEEN Date(?) AND Date(?))
           OR SES1.ses_StillConnected = 1
    """

    cur.execute(sql, (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date))
    rows = cur.fetchall()

    table_data = []
    for r in rows:
        row = dict(r)

        # Determine color
        if row["ses_EventTypeConnection"] == "<missing event>" or row["ses_EventTypeDisconnection"] == "<missing event>":
            color = "#f39c12"
        elif row["ses_StillConnected"] == 1:
            color = "#00a659"
        else:
            color = "#0073b7"

        # Tooltip
        tooltip = (
            f"Connection: {format_event_date(row['ses_DateTimeConnection'], row['ses_EventTypeConnection'])}\n"
            f"Disconnection: {format_event_date(row['ses_DateTimeDisconnection'], row['ses_EventTypeDisconnection'])}\n"
            f"IP: {row['ses_IP']}"
        )

        # Append calendar entry
        table_data.append({
            "resourceId": row["ses_MAC"],
            "title": "",
            "start": format_date_iso(row["ses_DateTimeConnectionCorrected"]),
            "end": format_date_iso(row["ses_DateTimeDisconnectionCorrected"]),
            "color": color,
            "tooltip": tooltip,
            "className": "no-border"
        })

    conn.close()
    return jsonify({"success": True, "sessions": table_data})