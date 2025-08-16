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
from helper import row_to_json, get_date_from_period, is_random_mac, format_date, get_setting_value


# --------------------------
# Device Endpoints Functions
# --------------------------

def delete_devices(macs):
    """
    Delete devices from the Devices table.
    - If `macs` is None → delete ALL devices.
    - If `macs` is a list → delete only matching MACs (supports wildcard '*').
    """

    conn = get_temp_db_connection()
    cur = conn.cursor()

    if not macs:
        # No MACs provided → delete all
        cur.execute("DELETE FROM Devices")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "deleted": "all"})

    deleted_count = 0

    for mac in macs:
        if "*" in mac:
            # Wildcard matching
            sql_pattern = mac.replace("*", "%")
            cur.execute("DELETE FROM Devices WHERE devMAC LIKE ?", (sql_pattern,))
        else:
            # Exact match
            cur.execute("DELETE FROM Devices WHERE devMAC = ?", (mac,))
        deleted_count += cur.rowcount

    conn.commit()
    conn.close()

    return jsonify({"success": True, "deleted_count": deleted_count})

def delete_all_with_empty_macs():
    """Delete devices with empty MAC addresses."""
    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Devices WHERE devMAC IS NULL OR devMAC = ''")
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return jsonify({"success": True, "deleted": deleted})

def delete_unknown_devices():
    """Delete devices marked as unknown."""
    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute("""DELETE FROM Devices WHERE devName='(unknown)' OR devName='(name not found)'""")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "deleted": cur.rowcount})