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