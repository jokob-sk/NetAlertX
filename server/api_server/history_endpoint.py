#!/usr/bin/env python

import os
import sys
from flask import jsonify

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection


# --------------------------------------------------
# Online History Activity Endpoints Functions
# --------------------------------------------------


def delete_online_history():
    """Delete all online history activity"""

    conn = get_temp_db_connection()
    cur = conn.cursor()

    sql = "DELETE FROM Online_History"
    cur.execute(sql)
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Deleted online history"})
