#!/usr/bin/env python

import json
import argparse
import os
import pathlib
import base64
import re
import sys
from datetime import datetime
from flask import jsonify, request, Response
import csv
import io
from io import StringIO

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection


def read_query(raw_sql_b64):
    """Execute a read-only query (SELECT)."""
    try:
        raw_sql = base64.b64decode(raw_sql_b64).decode("utf-8")

        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(raw_sql)
        rows = cur.fetchall()

        # Convert rows → dict list
        columns = [col[0] for col in cur.description] if cur.description else []
        results = [dict(zip(columns, row)) for row in rows]

        conn.close()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


def write_query(raw_sql_b64):
    """Execute a write query (INSERT/UPDATE/DELETE)."""
    try:
        raw_sql = base64.b64decode(raw_sql_b64).decode("utf-8")

        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(raw_sql)
        conn.commit()

        affected = cur.rowcount
        conn.close()
        return jsonify({"success": True, "affected_rows": affected})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


def update_query(column_name, ids, dbtable, columns, values):
    """Update rows in dbtable based on column_name + ids."""
    try:
        conn = get_temp_db_connection()
        cur = conn.cursor()

        if not isinstance(ids, list):
            ids = [ids]

        updated_count = 0
        for i in range(len(ids)):
            set_clause = ", ".join([f"{col} = ?" for col in columns])
            sql = f"UPDATE {dbtable} SET {set_clause} WHERE {column_name} = ?"
            params = list(values) + [ids[i]]
            cur.execute(sql, params)
            updated_count += cur.rowcount

        conn.commit()
        conn.close()
        return jsonify({"success": True, "updated_count": updated_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


def delete_query(column_name, ids, dbtable):
    """Delete rows in dbtable based on column_name + ids."""
    try:
        conn = get_temp_db_connection()
        cur = conn.cursor()

        if not isinstance(ids, list):
            ids = [ids]

        deleted_count = 0
        for id_val in ids:
            sql = f"DELETE FROM {dbtable} WHERE {column_name} = ?"
            cur.execute(sql, (id_val,))
            deleted_count += cur.rowcount

        conn.commit()
        conn.close()
        return jsonify({"success": True, "deleted_count": deleted_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400