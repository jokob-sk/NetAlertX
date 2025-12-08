#!/usr/bin/env python

import os
import base64
import re
import sys
import sqlite3
from flask import jsonify, request, Response
import csv
from io import StringIO
from logger import mylog

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection  # noqa: E402 [flake8 lint suppression]
from db.db_helper import get_table_json, get_device_condition_by_status  # noqa: E402 [flake8 lint suppression]


# --------------------------
# Device Endpoints Functions
# --------------------------
def get_all_devices():
    """Retrieve all devices from the database."""
    conn = get_temp_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Devices")
    rows = cur.fetchall()

    # Convert rows to list of dicts using column names
    columns = [col[0] for col in cur.description]
    devices = [dict(zip(columns, row)) for row in rows]

    conn.close()
    return jsonify({"success": True, "devices": devices})


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
    cur.execute(
        """DELETE FROM Devices WHERE devName='(unknown)' OR devName='(name not found)'"""
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "deleted": cur.rowcount})


def export_devices(export_format):
    """
    Export devices from the Devices table in the desired format.
    - If `macs` is None → delete ALL devices.
    - If `macs` is a list → delete only matching MACs (supports wildcard '*').
    """
    conn = get_temp_db_connection()
    cur = conn.cursor()

    # Fetch all devices
    devices_json = get_table_json(cur, "SELECT * FROM Devices")
    conn.close()

    # Ensure columns exist
    columns = devices_json.columnNames or (
        list(devices_json["data"][0].keys()) if devices_json["data"] else []
    )

    if export_format == "json":
        # Convert to standard dict for Flask JSON
        return jsonify(
            {"data": [row for row in devices_json["data"]], "columns": list(columns)}
        )
    elif export_format == "csv":
        si = StringIO()
        writer = csv.DictWriter(si, fieldnames=columns, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in devices_json.json["data"]:
            writer.writerow(row)

        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=devices.csv"},
        )
    else:
        return jsonify({"error": f"Unsupported format '{export_format}'"}), 400


def import_csv(file_storage=None):
    data = ""
    skipped = []

    # 1. Try JSON `content` (base64-encoded CSV)
    if request.is_json and request.json.get("content"):
        try:
            data = base64.b64decode(request.json["content"], validate=True).decode(
                "utf-8"
            )
        except Exception as e:
            return jsonify({"error": f"Base64 decode failed: {e}"}), 400

    # 2. Otherwise, try uploaded file
    elif file_storage:
        data = file_storage.read().decode("utf-8")

    # 3. Fallback: try local file (same as PHP `$file = '../../../config/devices.csv';`)
    else:
        config_root = os.environ.get("NETALERTX_CONFIG", "/data/config")
        local_file = os.path.join(config_root, "devices.csv")
        try:
            with open(local_file, "r", encoding="utf-8") as f:
                data = f.read()
        except FileNotFoundError:
            return jsonify({"error": "CSV file missing"}), 404

    if not data:
        return jsonify({"error": "No CSV data found"}), 400

    # --- Clean up newlines inside quoted fields ---
    data = re.sub(r'"([^"]*)"', lambda m: m.group(0).replace("\n", " "), data)

    # --- Parse CSV ---
    lines = data.splitlines()
    reader = csv.reader(lines)
    try:
        header = [h.strip() for h in next(reader)]
    except StopIteration:
        return jsonify({"error": "CSV missing header"}), 400

    # --- Wipe Devices table ---
    conn = get_temp_db_connection()
    sql = conn.cursor()
    sql.execute("DELETE FROM Devices")

    # --- Prepare insert ---
    placeholders = ",".join(["?"] * len(header))
    insert_sql = f"INSERT INTO Devices ({', '.join(header)}) VALUES ({placeholders})"

    row_count = 0
    for idx, row in enumerate(reader, start=1):
        if len(row) != len(header):
            skipped.append(idx)
            continue
        try:
            sql.execute(insert_sql, [col.strip() for col in row])
            row_count += 1
        except sqlite3.Error as e:
            mylog("error", [f"[ImportCSV] SQL ERROR row {idx}: {e}"])
            skipped.append(idx)

    conn.commit()
    conn.close()

    return jsonify({"success": True, "inserted": row_count, "skipped_lines": skipped})


def devices_totals():
    conn = get_temp_db_connection()
    sql = conn.cursor()

    # Build a combined query with sub-selects for each status
    query = f"""
    SELECT
        (SELECT COUNT(*) FROM Devices {get_device_condition_by_status("my")}) AS devices,
        (SELECT COUNT(*) FROM Devices {get_device_condition_by_status("connected")}) AS connected,
        (SELECT COUNT(*) FROM Devices {get_device_condition_by_status("favorites")}) AS favorites,
        (SELECT COUNT(*) FROM Devices {get_device_condition_by_status("new")}) AS new,
        (SELECT COUNT(*) FROM Devices {get_device_condition_by_status("down")}) AS down,
        (SELECT COUNT(*) FROM Devices {get_device_condition_by_status("archived")}) AS archived
    """
    sql.execute(query)
    row = (
        sql.fetchone()
    )  # returns a tuple like (devices, connected, favorites, new, down, archived)

    conn.close()

    # Return counts as JSON array
    return jsonify(list(row))


def devices_by_status(status=None):
    """
    Return devices filtered by status. Returns all if no status provided.
    Possible statuses: my, connected, favorites, new, down, archived
    """

    conn = get_temp_db_connection()
    sql = conn.cursor()

    # Build condition for SQL
    condition = get_device_condition_by_status(status) if status else ""

    query = f"SELECT * FROM Devices {condition}"
    sql.execute(query)

    table_data = []
    for row in sql.fetchall():
        r = dict(row)  # Convert sqlite3.Row to dict for .get()
        dev_name = r.get("devName", "")
        if r.get("devFavorite") == 1:
            dev_name = f'<span class="text-yellow">&#9733</span>&nbsp;{dev_name}'

        table_data.append(
            {
                "id": r.get("devMac", ""),
                "title": dev_name,
                "favorite": r.get("devFavorite", 0),
            }
        )

    conn.close()
    return jsonify(table_data)
