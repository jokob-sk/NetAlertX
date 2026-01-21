"""
Authoritative field update handler for NetAlertX.

This module enforces source-tracking policies when plugins or users update device fields.
It prevents overwrites when fields are marked as USER or LOCKED, and tracks the source
of each field value.

Author: NetAlertX Core
License: GNU GPLv3
"""

import sys
import os

INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]


# Map of field to its source tracking field
FIELD_SOURCE_MAP = {
    "devMac": "devMacSource",
    "devName": "devNameSource",
    "devFQDN": "devFqdnSource",
    "devLastIP": "devLastIpSource",
    "devVendor": "devVendorSource",
    "devSSID": "devSsidSource",
    "devParentMAC": "devParentMacSource",
    "devParentPort": "devParentPortSource",
    "devParentRelType": "devParentRelTypeSource",
    "devVlan": "devVlanSource",
}

# Fields that support source tracking
TRACKED_FIELDS = set(FIELD_SOURCE_MAP.keys())


def get_plugin_authoritative_settings(plugin_prefix):
    """
    Get SET_ALWAYS and SET_EMPTY settings for a plugin.

    Args:
        plugin_prefix: The unique prefix of the plugin (e.g., "UNIFIAPI").

    Returns:
        dict: {
            "set_always": [list of fields],
            "set_empty": [list of fields]
        }
    """
    try:
        set_always_key = f"{plugin_prefix}_SET_ALWAYS"
        set_empty_key = f"{plugin_prefix}_SET_EMPTY"

        set_always = get_setting_value(set_always_key) or []
        set_empty = get_setting_value(set_empty_key) or []

        # Normalize to list of strings if they aren't already
        if isinstance(set_always, str):
            set_always = [set_always]
        if isinstance(set_empty, str):
            set_empty = [set_empty]

        return {
            "set_always": list(set_always) if set_always else [],
            "set_empty": list(set_empty) if set_empty else [],
        }
    except Exception as e:
        mylog("debug", [f"[authoritative_handler] Failed to get settings for {plugin_prefix}: {e}"])
        return {"set_always": [], "set_empty": []}


def can_overwrite_field(field_name, current_source, plugin_prefix, plugin_settings, field_value):
    """
    Determine if a plugin can overwrite a field.

    Rules:
    - If current_source is USER or LOCKED, cannot overwrite.
    - If field_value is empty/None, cannot overwrite.
    - If field is in SET_ALWAYS, can overwrite.
    - If field is in SET_EMPTY AND current value is empty, can overwrite.
    - If neither SET_ALWAYS nor SET_EMPTY apply, can overwrite empty fields only.

    Args:
        field_name: The field being updated (e.g., "devName").
        current_source: The current source value (e.g., "USER", "LOCKED", "ARPSCAN", "NEWDEV", "").
        plugin_prefix: The unique prefix of the overwriting plugin.
        plugin_settings: dict with "set_always" and "set_empty" lists.
        field_value: The new value the plugin wants to write.

    Returns:
        bool: True if the overwrite is allowed, False otherwise.
    """

    # Rule 1: USER and LOCKED are protected
    if current_source in ("USER", "LOCKED"):
        return False

    # Rule 2: Plugin must provide a non-empty value
    if not field_value or (isinstance(field_value, str) and not field_value.strip()):
        return False

    # Rule 3: SET_ALWAYS takes precedence
    set_always = plugin_settings.get("set_always", [])
    if field_name in set_always:
        return True

    # Rule 4: SET_EMPTY allows overwriting only if field is empty
    set_empty = plugin_settings.get("set_empty", [])
    if field_name in set_empty:
        # Check if field is "empty" (no current source or NEWDEV)
        return not current_source or current_source == "NEWDEV"

    # Rule 5: Default behavior - overwrite if field is empty/NEWDEV
    return not current_source or current_source == "NEWDEV"


def get_source_for_field_update(field_name, plugin_prefix, is_user_override=False):
    """
    Determine what source value should be set when a field is updated.

    Args:
        field_name: The field being updated.
        plugin_prefix: The unique prefix of the plugin writing (e.g., "UNIFIAPI").
                       Ignored if is_user_override is True.
        is_user_override: If True, return "USER"; if False, return plugin_prefix.

    Returns:
        str: The source value to set for the *Source field.
    """
    if is_user_override:
        return "USER"
    return plugin_prefix


def enforce_source_on_user_update(devMac, updates_dict, conn):
    """
    When a user updates device fields, enforce source tracking.

    For each field with a corresponding *Source field:
    - If the field value is being changed, set the *Source to "USER".
    - If user explicitly locks a field, set the *Source to "LOCKED".

    Args:
        devMac: The MAC address of the device being updated.
        updates_dict: Dict of field -> value being updated.
        conn: Database connection object.
    """

    cur = conn.cursor()

    # Check if field has a corresponding source and should be updated
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(Devices)")
        device_columns = {row["name"] for row in cur.fetchall()}
    except Exception:
        device_columns = set()

    updates_to_apply = {}
    for field_name, new_value in updates_dict.items():
        if field_name in FIELD_SOURCE_MAP:
            source_field = FIELD_SOURCE_MAP[field_name]
            # User is updating this field, so mark it as USER
            if not device_columns or source_field in device_columns:
                updates_to_apply[source_field] = "USER"

    if not updates_to_apply:
        return

    # Build SET clause
    set_clause = ", ".join([f"{k}=?" for k in updates_to_apply.keys()])
    values = list(updates_to_apply.values())
    values.append(devMac)

    sql = f"UPDATE Devices SET {set_clause} WHERE devMac = ?"

    try:
        cur.execute(sql, values)
        conn.commit()
        mylog(
            "debug",
            [f"[enforce_source_on_user_update] Updated sources for {devMac}: {updates_to_apply}"],
        )
    except Exception as e:
        mylog("none", [f"[enforce_source_on_user_update] ERROR: {e}"])
        conn.rollback()
        raise


def lock_field(devMac, field_name, conn):
    """
    Lock a field so it won't be overwritten by plugins.

    Args:
        devMac: The MAC address of the device.
        field_name: The field to lock.
        conn: Database connection object.
    """

    if field_name not in FIELD_SOURCE_MAP:
        mylog("debug", [f"[lock_field] Field {field_name} does not support locking"])
        return

    source_field = FIELD_SOURCE_MAP[field_name]
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(Devices)")
        device_columns = {row["name"] for row in cur.fetchall()}
    except Exception:
        device_columns = set()

    if device_columns and source_field not in device_columns:
        mylog("debug", [f"[lock_field] Source column {source_field} missing for {field_name}"])
        return

    sql = f"UPDATE Devices SET {source_field}='LOCKED' WHERE devMac = ?"

    try:
        cur.execute(sql, (devMac,))
        conn.commit()
        mylog("debug", [f"[lock_field] Locked {field_name} for {devMac}"])
    except Exception as e:
        mylog("none", [f"[lock_field] ERROR: {e}"])
        conn.rollback()
        raise


def unlock_field(devMac, field_name, conn):
    """
    Unlock a field so plugins can overwrite it again.

    Args:
        devMac: The MAC address of the device.
        field_name: The field to unlock.
        conn: Database connection object.
    """

    if field_name not in FIELD_SOURCE_MAP:
        mylog("debug", [f"[unlock_field] Field {field_name} does not support unlocking"])
        return

    source_field = FIELD_SOURCE_MAP[field_name]
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(Devices)")
        device_columns = {row["name"] for row in cur.fetchall()}
    except Exception:
        device_columns = set()

    if device_columns and source_field not in device_columns:
        mylog("debug", [f"[unlock_field] Source column {source_field} missing for {field_name}"])
        return

    # Unlock by resetting to empty (allows overwrite)
    sql = f"UPDATE Devices SET {source_field}='' WHERE devMac = ?"

    try:
        cur.execute(sql, (devMac,))
        conn.commit()
        mylog("debug", [f"[unlock_field] Unlocked {field_name} for {devMac}"])
    except Exception as e:
        mylog("none", [f"[unlock_field] ERROR: {e}"])
        conn.rollback()
        raise
