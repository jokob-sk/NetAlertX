import json
import sys
import os

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from const import apiPath


def escape_label_value(val):
    """
    Escape special characters for Prometheus labels.
    """
    return str(val).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


# Define a base URL with the user's home directory
folder = apiPath


def get_metric_stats():
    output = []

    # 1. Dashboard totals
    try:
        with open(folder + "table_devices_tiles.json", "r") as f:
            tiles_data = json.load(f)["data"]

        if isinstance(tiles_data, list) and tiles_data:
            totals = tiles_data[0]
            output.append(f"netalertx_connected_devices {totals.get('connected', 0)}")
            output.append(f"netalertx_offline_devices {totals.get('offline', 0)}")
            output.append(f"netalertx_down_devices {totals.get('down', 0)}")
            output.append(f"netalertx_new_devices {totals.get('new', 0)}")
            output.append(f"netalertx_archived_devices {totals.get('archived', 0)}")
            output.append(f"netalertx_favorite_devices {totals.get('favorites', 0)}")
            output.append(f"netalertx_my_devices {totals.get('my_devices', 0)}")
        else:
            output.append("# Unexpected format in table_devices_tiles.json")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        mylog("none", f"[metrics] Error loading tiles data: {e}")
        output.append(f"# Error loading tiles data: {e}")
    except Exception as e:
        output.append(f"# General error loading dashboard totals: {e}")

    # 2. Device-level metrics
    try:
        with open(folder + "table_devices.json", "r") as f:
            data = json.load(f)

        devices = data.get("data", [])

        for row in devices:
            name = escape_label_value(row.get("devName", "unknown"))
            mac = escape_label_value(row.get("devMac", "unknown"))
            ip = escape_label_value(row.get("devLastIP", "unknown"))
            vendor = escape_label_value(row.get("devVendor", "unknown"))
            first_conn = escape_label_value(row.get("devFirstConnection", "unknown"))
            last_conn = escape_label_value(row.get("devLastConnection", "unknown"))
            dev_type = escape_label_value(row.get("devType", "unknown"))
            raw_status = row.get("devStatus", "Unknown")
            dev_status = raw_status.replace("-", "").capitalize()

            output.append(
                f'netalertx_device_status{{device="{name}", mac="{mac}", ip="{ip}", vendor="{vendor}", '
                f'first_connection="{first_conn}", last_connection="{last_conn}", dev_type="{dev_type}", '
                f'device_status="{dev_status}"}} 1'
            )

    except (FileNotFoundError, json.JSONDecodeError) as e:
        mylog("none", f"[metrics] Error loading devices data: {e}")
        output.append(f"# Error loading devices data: {e}")
    except Exception as e:
        output.append(f"# General error processing device metrics: {e}")

    return "\n".join(output) + "\n"
