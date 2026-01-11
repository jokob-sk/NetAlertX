import sys
import os
import requests
import sqlite3
import random
import argparse
from datetime import datetime

from pydantic import ValidationError

try:
    from api_server.schemas import (
        DeviceSearchResponse,
        DeviceListResponse,
        GetDeviceResponse,
        DeviceInfo,
        DeviceTotalsResponse,
        DeviceExportResponse,
        NetworkTopologyResponse,
        BaseResponse,
        OpenPortsResponse,
        WakeOnLanResponse,
        TracerouteResponse,
        RecentEventsResponse,
        LastEventsResponse,
        DbQueryResponse,
        GetSettingResponse
    )
    from const import fullDbPath
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Database Config
DB_PATH = fullDbPath


def _assert_db_exists(path: str) -> None:
    """Ensure the configured SQLite DB file exists before opening it."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Database file not found at {path}. Did you run initial setup?")


def get_db_connection():
    _assert_db_exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT setValue FROM Settings WHERE setKey = ?", (key,))
        row = cur.fetchone()
        return row['setValue'] if row else None
    except Exception as e:
        print(f"Error fetching setting {key}: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def find_test_device():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT devMAC, devLastIP FROM Devices WHERE devName = 'SchemaTestDevice' AND devOwner = 'Tester' LIMIT 1")
        row = cur.fetchone()
        if row:
            return row['devMAC'], row['devLastIP']
        return None, None
    except Exception as e:
        print(f"Error finding test device: {e}")
        return None, None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def remove_test_device(mac):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Devices WHERE devMAC = ?", (mac,))
        conn.commit()
    except Exception as e:
        print(f"Error removing test device {mac}: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def inject_test_device():
    # Use locally administered MAC address range
    mac = "02:%02x:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255), random.randint(0, 255), random.randint(0, 255),
        random.randint(0, 255), random.randint(0, 255))
    ip = "127.0.0.1"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if MAC exists (statistically impossible but good practice)
        cur.execute("SELECT devMAC FROM Devices WHERE devMAC = ?", (mac,))
        if cur.fetchone():
            return inject_test_device()  # Try again

        # Insert Device
        sql = """INSERT INTO Devices (
            devMAC, devName, devOwner, devFirstConnection, devLastConnection,
            devLastIP, devScan, devLogEvents, devAlertEvents, devIsNew, devVendor, devCustomProps
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        cur.execute(sql, (
            mac, "SchemaTestDevice", "Tester", now, now,
            ip, 1, 0, 0, 0, "TestVendor", "{}"
        ))
        conn.commit()
        print(f"Injected Test Device: {mac}")
        return mac, ip

    except Exception as e:
        print(f"Error injecting device: {e}")
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# Initialize
print("--- INITIALIZATION ---")

parser = argparse.ArgumentParser(description='Rigorous Schema Validation')
parser.add_argument('--inject-test-device', action='store_true', help='Inject a test device if not present')
parser.add_argument('--cleanup', action='store_true', help='Remove test device after validation')
args = parser.parse_args()

TOKEN = get_setting('API_TOKEN')
PORT = get_setting('GRAPHQL_PORT')

if not TOKEN or not PORT:
    print("Failed to retrieve config from DB")
    sys.exit(1)

BASE_URL = f"http://127.0.0.1:{PORT}"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
REQUEST_TIMEOUT = (5, 30)  # (connect, read)

MAC, IP = find_test_device()
MUST_CLEANUP = False

if not MAC:
    if args.inject_test_device:
        MAC, IP = inject_test_device()
        MUST_CLEANUP = args.cleanup
    else:
        # Fallback to a default if injection not requested and none found,
        # but the request says "only run when explicitly requested" for injection.
        # However, the script needs a MAC to run validate().
        # If no device found and no injection requested, we should probably exit or warn.
        print("No test device found and --inject-test-device not specified. Exiting.")
        sys.exit(0)
else:
    print(f"Reusing existing Test Device: {MAC}")
    MUST_CLEANUP = args.cleanup


def validate(endpoint, method, model, payload=None):
    print(f"Testing {method} {endpoint} -> {model.__name__}...", end=" ")
    r = None
    data = None
    try:
        url = f"{BASE_URL}{endpoint}"
        method_upper = method.upper()
        if method_upper == "GET":
            r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        elif method_upper == "POST":
            r = requests.post(url, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
        elif method_upper == "DELETE":
            r = requests.delete(url, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
        else:
            print(f"FAIL (Unsupported method {method})")
            return False

        if r is None:
            print("FAIL (No response object)")
            return False

        if r.status_code not in (200, 202):
            print(f"FAIL (HTTP {r.status_code}): {r.text}")
            return False

        data = r.json()
        model.model_validate(data)
        print("PASS")
        return True

    except ValidationError as e:
        print(f"FAIL (Schema Mismatch): {e}")
        actual_keys = list(data.keys()) if isinstance(data, dict) else []
        print(f"Actual Data Keys: {actual_keys}")
        return False
    except requests.RequestException as e:
        print(f"FAIL (Request Error): {e}")
        return False
    except Exception as e:
        print(f"FAIL (Exception): {e}")
        return False


# --- EXECUTION ---
print("--- RIGOROUS SCHEMA VALIDATION ---")

# 1. Devices
validate(f"/device/{MAC}", "GET", DeviceInfo)  # Raw
validate("/devices/search", "POST", DeviceSearchResponse, {"query": IP})
validate("/devices/by-status", "POST", DeviceListResponse, {"status": "online"})
validate("/devices/totals", "GET", DeviceTotalsResponse)
validate("/devices/latest", "GET", GetDeviceResponse)  # Wrapped
validate("/devices/network/topology", "GET", NetworkTopologyResponse)
validate("/devices/export?format=json", "GET", DeviceExportResponse)   # Raw JSON export

# 2. Actions (BaseResponse)
validate(f"/device/{MAC}/set-alias", "POST", BaseResponse, {"alias": "SecurityTest"})
validate(f"/device/{MAC}/update-column", "POST", BaseResponse, {"columnName": "devComments", "columnValue": "Schema Check"})

# 3. NetTools
validate("/nettools/wakeonlan", "POST", WakeOnLanResponse, {"devMac": MAC})
validate("/nettools/traceroute", "POST", TracerouteResponse, {"devLastIP": IP})
validate("/device/open_ports", "POST", OpenPortsResponse, {"target": IP})

# 4. Events & Sessions
validate("/events/recent", "GET", RecentEventsResponse)
validate("/events/last", "GET", LastEventsResponse)
validate(f"/sessions/list?mac={MAC}", "GET", BaseResponse)
validate("/sessions/create", "POST", BaseResponse, {"mac": MAC, "ip": IP, "start_time": "2026-01-01 12:00:00"})
validate(f"/events/create/{MAC}", "POST", BaseResponse, {"event_type": "Test", "ip": IP})

# 5. System
validate("/dbquery/read", "POST", DbQueryResponse, {"rawSql": "U0VMRUNUICogRlJPTSBEZXZpY2VzIExJTUlUIDE=", "confirm_dangerous_query": True})
validate("/settings/API_TOKEN", "GET", GetSettingResponse)

if MUST_CLEANUP:
    print(f"--- CLEANUP: Removing Test Device {MAC} ---")
    remove_test_device(MAC)

print("--- DONE ---")
