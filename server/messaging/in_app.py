import os
import sys
import _io
import json
import uuid
import time

from flask import jsonify

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from const import apiPath  # noqa: E402 [flake8 lint suppression]
from logger import mylog  # noqa: E402 [flake8 lint suppression]
from utils.datetime_utils import timeNowDB  # noqa: E402 [flake8 lint suppression]
from api_server.sse_broadcast import broadcast_unread_notifications_count  # noqa: E402 [flake8 lint suppression]


NOTIFICATION_API_FILE = apiPath + 'user_notifications.json'


# Show Frontend User Notification
def write_notification(content, level="alert", timestamp=None):
    """
    Create and append a new user notification entry to the notifications file.

    Args:
        content (str): The message content to display to the user.
        level (str, optional): Notification severity (e.g., 'info', 'alert', 'warning').
                               Defaults to 'alert'.
        timestamp (datetime, optional): Custom timestamp; if None, uses current time.

    Returns:
        None
    """
    if timestamp is None:
        timestamp = timeNowDB()

    # Generate GUID
    guid = str(uuid.uuid4())

    # Prepare notification dictionary
    notification = {
        "timestamp": str(timestamp),
        "guid": guid,
        "read": 0,
        "level": level,
        "content": content,
    }

    # If file exists, load existing data, otherwise initialize as empty list
    if os.path.exists(NOTIFICATION_API_FILE):
        with open(NOTIFICATION_API_FILE, "r") as file:
            # Check if the file object is of type _io.TextIOWrapper
            if isinstance(file, _io.TextIOWrapper):
                file_contents = file.read()  # Read file contents
                if file_contents == "":
                    file_contents = "[]"  # If file is empty, initialize as empty list

                # mylog('debug', ['[Notification] User Notifications file: ', file_contents])
                notifications = json.loads(file_contents)  # Parse JSON data
            else:
                mylog("none", "[Notification] File is not of type _io.TextIOWrapper")
                notifications = []
    else:
        notifications = []

    # Append new notification
    notifications.append(notification)

    # Write updated data back to file
    with open(NOTIFICATION_API_FILE, "w") as file:
        json.dump(notifications, file, indent=4)

    # Broadcast unread count update
    try:
        unread_count = sum(1 for n in notifications if n.get("read", 0) == 0)
        broadcast_unread_notifications_count(unread_count)
    except Exception as e:
        mylog("none", [f"[Notification] Failed to broadcast unread count: {e}"])


# Trim notifications
def remove_old(keepNumberOfEntries):
    """
    Trim the notifications file, keeping only the most recent N entries.

    Args:
        keepNumberOfEntries (int): Number of latest notifications to retain.

    Returns:
        None
    """
    # Check if file exists
    if not os.path.exists(NOTIFICATION_API_FILE):
        mylog("info", "[Notification] No notifications file to clean.")
        return

    # Load existing notifications
    try:
        with open(NOTIFICATION_API_FILE, "r") as file:
            file_contents = file.read().strip()
            if file_contents == "":
                notifications = []
            else:
                notifications = json.loads(file_contents)
    except Exception as e:
        mylog("none", f"[Notification] Error reading notifications file: {e}")
        return

    if not isinstance(notifications, list):
        mylog("none", "[Notification] Invalid format: not a list")
        return

    # Sort by timestamp descending
    try:
        notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    except KeyError:
        mylog("none", "[Notification] Missing timestamp in one or more entries")
        return

    # Trim to the latest entries
    trimmed = notifications[:keepNumberOfEntries]

    # Write back the trimmed list
    try:
        with open(NOTIFICATION_API_FILE, "w") as file:
            json.dump(trimmed, file, indent=4)
        mylog("verbose", f"[Notification] Trimmed notifications to latest {keepNumberOfEntries}",)
    except Exception as e:
        mylog("none", f"Error writing trimmed notifications file: {e}")


def mark_all_notifications_read():
    """
    Mark all existing notifications as read.

    Returns:
        dict: JSON-compatible dictionary containing:
            {
                "success": bool,
                "error": str (optional)
            }
    """
    if not os.path.exists(NOTIFICATION_API_FILE):
        return {"success": True}

    try:
        with open(NOTIFICATION_API_FILE, "r") as f:
            notifications = json.load(f)
    except Exception as e:
        mylog("none", f"[Notification] Failed to read notifications: {e}")
        return {"success": False, "error": str(e)}

    for n in notifications:
        n["read"] = 1

    try:
        with open(NOTIFICATION_API_FILE, "w") as f:
            json.dump(notifications, f, indent=4)
    except Exception as e:
        mylog("none", f"[Notification] Failed to write notifications: {e}")
        return {"success": False, "error": str(e)}

    mylog("debug", "[Notification] All notifications marked as read.")

    # Broadcast unread count update
    try:
        broadcast_unread_notifications_count(0)
    except Exception as e:
        mylog("none", [f"[Notification] Failed to broadcast unread count: {e}"])

    return {"success": True}


def delete_notifications():
    """
    Delete all notifications from the JSON file.

    Returns:
        A JSON response with {"success": True}.
    """
    with open(NOTIFICATION_API_FILE, "w") as f:
        json.dump([], f, indent=4)
        mylog("debug", "[Notification] All notifications deleted.")

    # Broadcast unread count update
    try:
        broadcast_unread_notifications_count(0)
    except Exception as e:
        mylog("none", [f"[Notification] Failed to broadcast unread count: {e}"])

    return jsonify({"success": True})


def get_unread_notifications():
    """
    Retrieve all unread notifications from the JSON file.

    Returns:
        A JSON array of unread notification objects.
    """
    if not os.path.exists(NOTIFICATION_API_FILE):
        return jsonify([])

    with open(NOTIFICATION_API_FILE, "r") as f:
        notifications = json.load(f)

    unread = [n for n in notifications if n.get("read", 0) == 0]
    return jsonify(unread)


def mark_notification_as_read(guid=None, max_attempts=3):
    """
    Mark a notification as read based on GUID.
    If guid is None, mark all notifications as read.

    Args:
        guid (str, optional): The GUID of the notification to mark. Defaults to None.
        max_attempts (int, optional): Number of attempts to read/write file. Defaults to 3.

    Returns:
        dict: {"success": True} on success, {"success": False, "error": "..."} on failure
    """
    attempts = 0

    while attempts < max_attempts:
        try:
            if os.path.exists(NOTIFICATION_API_FILE) and os.access(
                NOTIFICATION_API_FILE, os.R_OK | os.W_OK
            ):
                with open(NOTIFICATION_API_FILE, "r") as f:
                    notifications = json.load(f)

                if notifications is not None:
                    for notification in notifications:
                        if guid is None or notification.get("guid") == guid:
                            notification["read"] = 1

                    with open(NOTIFICATION_API_FILE, "w") as f:
                        json.dump(notifications, f, indent=4)

                    # Broadcast unread count update
                    try:
                        unread_count = sum(1 for n in notifications if n.get("read", 0) == 0)
                        broadcast_unread_notifications_count(unread_count)
                    except Exception as e:
                        mylog("none", [f"[Notification] Failed to broadcast unread count: {e}"])

                    return {"success": True}
        except Exception as e:
            mylog("none", f"[Notification] Attempt {attempts + 1} failed: {e}")

        attempts += 1
        time.sleep(0.5)  # Sleep 0.5 seconds before retrying

    error_msg = f"Failed to read/write notification file after {max_attempts} attempts."
    mylog("none", f"[Notification] {error_msg}")
    return {"success": False, "error": error_msg}


def delete_notification(guid):
    """
    Delete a notification from the notifications file based on its GUID.

    Args:
        guid (str): The GUID of the notification to delete.

    Returns:
        dict: {"success": True} on success, {"success": False, "error": "..."} on failure
    """
    if not guid:
        return {"success": False, "error": "GUID is required"}

    if not os.path.exists(NOTIFICATION_API_FILE):
        return {"success": True}  # Nothing to delete

    try:
        with open(NOTIFICATION_API_FILE, "r") as f:
            notifications = json.load(f)

        # Filter out the notification with the specified GUID
        filtered_notifications = [n for n in notifications if n.get("guid") != guid]

        # Write the updated notifications back
        with open(NOTIFICATION_API_FILE, "w") as f:
            json.dump(filtered_notifications, f, indent=4)

        # Broadcast unread count update
        try:
            unread_count = sum(1 for n in filtered_notifications if n.get("read", 0) == 0)
            broadcast_unread_notifications_count(unread_count)
        except Exception as e:
            mylog("none", [f"[Notification] Failed to broadcast unread count: {e}"])

        return {"success": True}

    except Exception as e:
        mylog("none", f"[Notification] Failed to delete notification {guid}: {e}")
        return {"success": False, "error": str(e)}
