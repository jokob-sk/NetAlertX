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
from helper import is_random_mac, format_date, get_setting_value
from db.db_helper import row_to_json


# --------------------------
# Events Endpoints Functions
# --------------------------

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

def delete_events_30():
    """Delete all events older than 30 days"""

    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = "DELETE FROM Events WHERE eve_DateTime <= date('now', '-30 day')"
    cur.execute(sql)
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Deleted events older than 30 days"})

def delete_events():
    """Delete all events"""

    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = "DELETE FROM Events"
    cur.execute(sql)
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Deleted all events"})


