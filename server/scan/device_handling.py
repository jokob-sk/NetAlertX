import subprocess
import os
import re
from helper import get_setting_value, check_IP_format
from utils.datetime_utils import timeNowDB, normalizeTimeStamp
from logger import mylog, Logger
from const import vendorsPath, vendorsPathNewest, sql_generateGuid
from models.device_instance import DeviceInstance
from scan.name_resolution import NameResolver
from scan.device_heuristics import guess_icon, guess_type
from db.db_helper import sanitize_SQL_input, list_to_where, safe_int
from db.authoritative_handler import (
    get_overwrite_sql_clause,
    get_plugin_authoritative_settings,
    get_source_for_field_update_with_value,
)
from helper import format_ip_long

# Make sure log level is initialized correctly
Logger(get_setting_value("LOG_LEVEL"))


# -------------------------------------------------------------------------------
# Removing devices from the CurrentScan DB table which the user chose to ignore by MAC or IP
def exclude_ignored_devices(db):
    sql = db.sql  # Database interface for executing queries

    mac_condition = list_to_where(
        "OR", "cur_MAC", "LIKE", get_setting_value("NEWDEV_ignored_MACs")
    )
    ip_condition = list_to_where(
        "OR", "cur_IP", "LIKE", get_setting_value("NEWDEV_ignored_IPs")
    )

    # Only delete if either the MAC or IP matches an ignored condition
    conditions = []
    if mac_condition:
        conditions.append(mac_condition)
    if ip_condition:
        conditions.append(ip_condition)

    # Join conditions and prepare the query
    conditions_str = " OR ".join(conditions)
    if conditions_str:
        query = f"""DELETE FROM CurrentScan WHERE
                        1=1
                        AND (
                            {conditions_str}
                        )
                """
    else:
        query = "DELETE FROM CurrentScan WHERE 1=1 AND 1=0"  # No valid conditions, prevent deletion

    mylog("debug", f"[New Devices] Excluding Ignored Devices Query: {query}")

    sql.execute(query)


# -------------------------------------------------------------------------------
def update_devices_data_from_scan(db):
    sql = db.sql  # TO-DO
    startTime = timeNowDB()

    device_columns = set()
    try:
        device_columns = {row["name"] for row in sql.execute("PRAGMA table_info(Devices)").fetchall()}
    except Exception:
        device_columns = set()

    def has_column(column_name):
        return column_name in device_columns if device_columns else False

    # Update Last Connection
    mylog("debug", "[Update Devices] 1 Last Connection")
    sql.execute(f"""UPDATE Devices SET devLastConnection = '{startTime}',
                        devPresentLastScan = 1
                    WHERE EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE devMac = cur_MAC) """)

    # Clean no active devices
    mylog("debug", "[Update Devices] 2 Clean no active devices")
    sql.execute("""UPDATE Devices SET devPresentLastScan = 0
                    WHERE NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE devMac = cur_MAC) """)

    plugin_rows = sql.execute(
        "SELECT DISTINCT cur_ScanMethod FROM CurrentScan"
    ).fetchall()
    plugin_prefixes = [row[0] for row in plugin_rows if row[0]]
    if not plugin_prefixes:
        plugin_prefixes = [None]
    plugin_settings_cache = {}

    def get_plugin_settings_cached(plugin_prefix):
        if plugin_prefix not in plugin_settings_cache:
            plugin_settings_cache[plugin_prefix] = get_plugin_authoritative_settings(
                plugin_prefix
            )
        return plugin_settings_cache[plugin_prefix]

    for plugin_prefix in plugin_prefixes:
        filter_by_scan_method = plugin_prefix is not None and plugin_prefix != ""
        source_prefix = plugin_prefix if filter_by_scan_method else "NEWDEV"
        plugin_settings = get_plugin_settings_cached(source_prefix)

        has_last_ip_source = has_column("devLastIpSource")
        has_vendor_source = has_column("devVendorSource")
        has_parent_port_source = has_column("devParentPortSource")
        has_parent_mac_source = has_column("devParentMacSource")
        has_ssid_source = has_column("devSsidSource")
        has_name_source = has_column("devNameSource")

        dev_last_ip_clause = (
            get_overwrite_sql_clause("devLastIP", "devLastIpSource", plugin_settings)
            if has_last_ip_source
            else "1=1"
        )
        dev_vendor_clause = (
            get_overwrite_sql_clause("devVendor", "devVendorSource", plugin_settings)
            if has_vendor_source
            else "1=1"
        )
        dev_parent_port_clause = (
            get_overwrite_sql_clause("devParentPort", "devParentPortSource", plugin_settings)
            if has_parent_port_source
            else "1=1"
        )
        dev_parent_mac_clause = (
            get_overwrite_sql_clause("devParentMAC", "devParentMacSource", plugin_settings)
            if has_parent_mac_source
            else "1=1"
        )
        dev_ssid_clause = (
            get_overwrite_sql_clause("devSSID", "devSsidSource", plugin_settings)
            if has_ssid_source
            else "1=1"
        )
        dev_name_clause = (
            get_overwrite_sql_clause("devName", "devNameSource", plugin_settings)
            if has_name_source
            else "1=1"
        )

        name_is_set_always = "devName" in plugin_settings.get("set_always", [])
        vendor_is_set_always = "devVendor" in plugin_settings.get("set_always", [])
        parent_port_is_set_always = "devParentPort" in plugin_settings.get("set_always", [])
        parent_mac_is_set_always = "devParentMAC" in plugin_settings.get("set_always", [])
        ssid_is_set_always = "devSSID" in plugin_settings.get("set_always", [])

        name_empty_condition = "1=1" if name_is_set_always else (
            "(devName IN ('(unknown)', '(name not found)', '') OR devName IS NULL)"
        )
        vendor_empty_condition = "1=1" if vendor_is_set_always else (
            "(devVendor IS NULL OR devVendor IN ('', 'null', '(unknown)', '(Unknown)'))"
        )
        parent_port_empty_condition = "1=1" if parent_port_is_set_always else (
            "(devParentPort IS NULL OR devParentPort IN ('', 'null', '(unknown)', '(Unknown)'))"
        )
        parent_mac_empty_condition = "1=1" if parent_mac_is_set_always else (
            "(devParentMAC IS NULL OR devParentMAC IN ('', 'null', '(unknown)', '(Unknown)'))"
        )
        ssid_empty_condition = "1=1" if ssid_is_set_always else (
            "(devSSID IS NULL OR devSSID IN ('', 'null'))"
        )

        # Update IP (devLastIP always updated, primary IPv4/IPv6 set based on family)
        mylog(
            "debug",
            f"[Update Devices] - ({source_prefix}) cur_IP -> devLastIP / devPrimaryIPv4 / devPrimaryIPv6",
        )
        last_ip_source_fragment = ", devLastIpSource = ?" if has_last_ip_source else ""
        last_ip_params = (source_prefix,) if has_last_ip_source else ()

        if filter_by_scan_method:
            sql.execute(
                f"""
                WITH LatestIP AS (
                    SELECT c.cur_MAC AS mac, c.cur_IP AS ip
                    FROM CurrentScan c
                    WHERE c.cur_IP IS NOT NULL
                      AND c.cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
                      AND c.cur_ScanMethod = ?
                      AND c.cur_DateTime = (
                          SELECT MAX(c2.cur_DateTime)
                          FROM CurrentScan c2
                          WHERE c2.cur_MAC = c.cur_MAC
                            AND c2.cur_IP IS NOT NULL
                            AND c2.cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
                            AND c2.cur_ScanMethod = ?
                      )
                )
                UPDATE Devices
                SET devLastIP = (SELECT ip FROM LatestIP WHERE mac = devMac),
                    devPrimaryIPv4 = CASE
                        WHEN (SELECT ip FROM LatestIP WHERE mac = devMac) LIKE '%:%' THEN devPrimaryIPv4
                        ELSE (SELECT ip FROM LatestIP WHERE mac = devMac)
                    END,
                    devPrimaryIPv6 = CASE
                        WHEN (SELECT ip FROM LatestIP WHERE mac = devMac) LIKE '%:%' THEN (SELECT ip FROM LatestIP WHERE mac = devMac)
                        ELSE devPrimaryIPv6
                    END
                    {last_ip_source_fragment}
                WHERE EXISTS (SELECT 1 FROM LatestIP WHERE mac = devMac)
                  AND {dev_last_ip_clause};
            """,
                (plugin_prefix, plugin_prefix, *last_ip_params),
            )
        else:
            sql.execute(
                f"""
                WITH LatestIP AS (
                    SELECT c.cur_MAC AS mac, c.cur_IP AS ip
                    FROM CurrentScan c
                    WHERE c.cur_IP IS NOT NULL
                      AND c.cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
                      AND c.cur_DateTime = (
                          SELECT MAX(c2.cur_DateTime)
                          FROM CurrentScan c2
                          WHERE c2.cur_MAC = c.cur_MAC
                            AND c2.cur_IP IS NOT NULL
                            AND c2.cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
                      )
                )
                UPDATE Devices
                SET devLastIP = (SELECT ip FROM LatestIP WHERE mac = devMac),
                    devPrimaryIPv4 = CASE
                        WHEN (SELECT ip FROM LatestIP WHERE mac = devMac) LIKE '%:%' THEN devPrimaryIPv4
                        ELSE (SELECT ip FROM LatestIP WHERE mac = devMac)
                    END,
                    devPrimaryIPv6 = CASE
                        WHEN (SELECT ip FROM LatestIP WHERE mac = devMac) LIKE '%:%' THEN (SELECT ip FROM LatestIP WHERE mac = devMac)
                        ELSE devPrimaryIPv6
                    END
                    {last_ip_source_fragment}
                WHERE EXISTS (SELECT 1 FROM LatestIP WHERE mac = devMac)
                  AND {dev_last_ip_clause};
            """,
                last_ip_params,
            )

        # Update vendor
        mylog("debug", f"[Update Devices] - ({source_prefix}) cur_Vendor -> devVendor")
        vendor_source_fragment = ", devVendorSource = ?" if has_vendor_source else ""
        vendor_params = (source_prefix,) if has_vendor_source else ()

        if filter_by_scan_method:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devVendor = (
                        SELECT cur_Vendor
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_ScanMethod = ?
                          AND CurrentScan.cur_Vendor IS NOT NULL
                          AND CurrentScan.cur_Vendor NOT IN ('', 'null', '(unknown)', '(Unknown)')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {vendor_source_fragment}
                    WHERE {vendor_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_ScanMethod = ?
                            AND CurrentScan.cur_Vendor IS NOT NULL
                            AND CurrentScan.cur_Vendor NOT IN ('', 'null', '(unknown)', '(Unknown)')
                      )
                      AND {dev_vendor_clause}
                """,
                (plugin_prefix, plugin_prefix, *vendor_params),
            )
        else:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devVendor = (
                        SELECT cur_Vendor
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_Vendor IS NOT NULL
                          AND CurrentScan.cur_Vendor NOT IN ('', 'null', '(unknown)', '(Unknown)')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {vendor_source_fragment}
                    WHERE {vendor_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_Vendor IS NOT NULL
                            AND CurrentScan.cur_Vendor NOT IN ('', 'null', '(unknown)', '(Unknown)')
                      )
                      AND {dev_vendor_clause}
                """,
                vendor_params,
            )

        # Update parent port
        mylog("debug", f"[Update Devices] - ({source_prefix}) cur_Port -> devParentPort")
        parent_port_source_fragment = ", devParentPortSource = ?" if has_parent_port_source else ""
        parent_port_params = (source_prefix,) if has_parent_port_source else ()

        if filter_by_scan_method:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devParentPort = (
                        SELECT cur_Port
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_ScanMethod = ?
                          AND CurrentScan.cur_Port IS NOT NULL
                          AND CurrentScan.cur_Port NOT IN ('', 'null')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {parent_port_source_fragment}
                    WHERE {parent_port_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_ScanMethod = ?
                            AND CurrentScan.cur_Port IS NOT NULL
                            AND CurrentScan.cur_Port NOT IN ('', 'null')
                      )
                      AND {dev_parent_port_clause}
                """,
                (plugin_prefix, plugin_prefix, *parent_port_params),
            )
        else:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devParentPort = (
                        SELECT cur_Port
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_Port IS NOT NULL
                          AND CurrentScan.cur_Port NOT IN ('', 'null')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {parent_port_source_fragment}
                    WHERE {parent_port_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_Port IS NOT NULL
                            AND CurrentScan.cur_Port NOT IN ('', 'null')
                      )
                      AND {dev_parent_port_clause}
                """,
                parent_port_params,
            )

        # Update parent MAC
        mylog("debug", f"[Update Devices] - ({source_prefix}) cur_NetworkNodeMAC -> devParentMAC")
        parent_mac_source_fragment = ", devParentMacSource = ?" if has_parent_mac_source else ""
        parent_mac_params = (source_prefix,) if has_parent_mac_source else ()

        if filter_by_scan_method:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devParentMAC = (
                        SELECT cur_NetworkNodeMAC
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_ScanMethod = ?
                          AND CurrentScan.cur_NetworkNodeMAC IS NOT NULL
                          AND CurrentScan.cur_NetworkNodeMAC NOT IN ('', 'null')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {parent_mac_source_fragment}
                    WHERE {parent_mac_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_ScanMethod = ?
                            AND CurrentScan.cur_NetworkNodeMAC IS NOT NULL
                            AND CurrentScan.cur_NetworkNodeMAC NOT IN ('', 'null')
                      )
                      AND {dev_parent_mac_clause}
                """,
                (plugin_prefix, plugin_prefix, *parent_mac_params),
            )
        else:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devParentMAC = (
                        SELECT cur_NetworkNodeMAC
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_NetworkNodeMAC IS NOT NULL
                          AND CurrentScan.cur_NetworkNodeMAC NOT IN ('', 'null')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {parent_mac_source_fragment}
                    WHERE {parent_mac_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_NetworkNodeMAC IS NOT NULL
                            AND CurrentScan.cur_NetworkNodeMAC NOT IN ('', 'null')
                      )
                      AND {dev_parent_mac_clause}
                """,
                parent_mac_params,
            )

        # Update SSID
        mylog("debug", f"[Update Devices] - ({source_prefix}) cur_SSID -> devSSID")
        ssid_source_fragment = ", devSsidSource = ?" if has_ssid_source else ""
        ssid_params = (source_prefix,) if has_ssid_source else ()

        if filter_by_scan_method:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devSSID = (
                        SELECT cur_SSID
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_ScanMethod = ?
                          AND CurrentScan.cur_SSID IS NOT NULL
                          AND CurrentScan.cur_SSID NOT IN ('', 'null')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {ssid_source_fragment}
                    WHERE {ssid_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_ScanMethod = ?
                            AND CurrentScan.cur_SSID IS NOT NULL
                            AND CurrentScan.cur_SSID NOT IN ('', 'null')
                      )
                      AND {dev_ssid_clause}
                """,
                (plugin_prefix, plugin_prefix, *ssid_params),
            )
        else:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devSSID = (
                        SELECT cur_SSID
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                          AND CurrentScan.cur_SSID IS NOT NULL
                          AND CurrentScan.cur_SSID NOT IN ('', 'null')
                        ORDER BY CurrentScan.cur_DateTime DESC
                        LIMIT 1
                    )
                        {ssid_source_fragment}
                    WHERE {ssid_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE Devices.devMac = CurrentScan.cur_MAC
                            AND CurrentScan.cur_SSID IS NOT NULL
                            AND CurrentScan.cur_SSID NOT IN ('', 'null')
                      )
                      AND {dev_ssid_clause}
                """,
                ssid_params,
            )

        # Update Name
        mylog("debug", f"[Update Devices] - ({source_prefix}) cur_Name -> devName")
        name_source_fragment = ", devNameSource = ?" if has_name_source else ""
        name_params = (source_prefix,) if has_name_source else ()

        if filter_by_scan_method:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devName = (
                        SELECT cur_Name
                        FROM CurrentScan
                        WHERE cur_MAC = devMac
                          AND cur_ScanMethod = ?
                          AND cur_Name IS NOT NULL
                          AND cur_Name <> 'null'
                          AND cur_Name <> ''
                        ORDER BY cur_DateTime DESC
                        LIMIT 1
                    )
                        {name_source_fragment}
                    WHERE {name_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE cur_MAC = devMac
                            AND cur_ScanMethod = ?
                            AND cur_Name IS NOT NULL
                            AND cur_Name <> 'null'
                            AND cur_Name <> ''
                      )
                      AND {dev_name_clause}
                """,
                (plugin_prefix, plugin_prefix, *name_params),
            )
        else:
            sql.execute(
                f"""
                UPDATE Devices
                    SET devName = (
                        SELECT cur_Name
                        FROM CurrentScan
                        WHERE cur_MAC = devMac
                          AND cur_Name IS NOT NULL
                          AND cur_Name <> 'null'
                          AND cur_Name <> ''
                        ORDER BY cur_DateTime DESC
                        LIMIT 1
                    )
                        {name_source_fragment}
                    WHERE {name_empty_condition}
                      AND EXISTS (
                          SELECT 1
                          FROM CurrentScan
                          WHERE cur_MAC = devMac
                            AND cur_Name IS NOT NULL
                            AND cur_Name <> 'null'
                            AND cur_Name <> ''
                      )
                      AND {dev_name_clause}
                """,
                name_params,
            )

    # Update only devices with empty or NULL devSite
    mylog("debug", "[Update Devices] - (if not empty) cur_NetworkSite -> (if empty) devSite",)
    sql.execute("""UPDATE Devices
                    SET devSite = (
                        SELECT cur_NetworkSite
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE
                        (devSite IS NULL OR devSite IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                                AND CurrentScan.cur_NetworkSite IS NOT NULL AND CurrentScan.cur_NetworkSite NOT IN ("", "null")
                )""")

    # Update only devices with empty or NULL devType
    mylog("debug", "[Update Devices] - (if not empty) cur_Type -> (if empty) devType")
    sql.execute("""UPDATE Devices
                    SET devType = (
                        SELECT cur_Type
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE
                        (devType IS NULL OR devType IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                                AND CurrentScan.cur_Type IS NOT NULL AND CurrentScan.cur_Type NOT IN ("", "null")
                        )""")

    # Update VENDORS
    recordsToUpdate = []
    vendor_settings = get_plugin_authoritative_settings("VNDRPDT")
    vendor_clause = (
        get_overwrite_sql_clause("devVendor", "devVendorSource", vendor_settings)
        if has_column("devVendorSource")
        else "1=1"
    )
    vendor_is_set_always = "devVendor" in vendor_settings.get("set_always", [])

    if vendor_is_set_always:
        query = f"""SELECT * FROM Devices
                   WHERE {vendor_clause}
                """
    else:
        query = f"""SELECT * FROM Devices
                   WHERE (devVendor IS NULL OR devVendor IN ("", "null", "(unknown)", "(Unknown)"))
                     AND {vendor_clause}
                """

    for device in sql.execute(query):
        vendor = query_MAC_vendor(device["devMac"])
        if vendor != -1 and vendor != -2:
            recordsToUpdate.append([vendor, "VNDRPDT", device["devMac"]])

    if len(recordsToUpdate) > 0:
        if has_column("devVendorSource"):
            sql.executemany(
                f"""UPDATE Devices
                    SET devVendor = ?,
                        devVendorSource = ?
                    WHERE devMac = ?
                      AND {vendor_clause}""",
                recordsToUpdate,
            )
        else:
            sql.executemany(
                """UPDATE Devices
                    SET devVendor = ?
                    WHERE devMac = ?""",
                [(row[0], row[2]) for row in recordsToUpdate],
            )

    # Update devPresentLastScan based on NICs presence
    update_devPresentLastScan_based_on_nics(db)

    # Force device status if configured
    update_devPresentLastScan_based_on_force_status(db)

    # Guess ICONS
    recordsToUpdate = []

    default_icon = get_setting_value("NEWDEV_devIcon")

    if get_setting_value("NEWDEV_replace_preset_icon"):
        query = f"""SELECT * FROM Devices
                    WHERE devIcon in ('', 'null', '{default_icon}')
                        OR devIcon IS NULL"""
    else:
        query = """SELECT * FROM Devices
                    WHERE devIcon in ('', 'null')
                        OR devIcon IS NULL"""

    for device in sql.execute(query):
        # Conditional logic for devIcon guessing
        devIcon = guess_icon(
            device["devVendor"],
            device["devMac"],
            device["devLastIP"],
            device["devName"],
            default_icon,
        )

        recordsToUpdate.append([devIcon, device["devMac"]])

    mylog("debug", f"[Update Devices] recordsToUpdate: {recordsToUpdate}")

    if len(recordsToUpdate) > 0:
        sql.executemany(
            "UPDATE Devices SET devIcon = ? WHERE devMac = ? ", recordsToUpdate
        )

    # Guess Type
    recordsToUpdate = []
    query = """SELECT * FROM Devices
                    WHERE devType in ('', 'null')
                OR devType IS NULL"""
    default_type = get_setting_value("NEWDEV_devType")

    for device in sql.execute(query):
        # Conditional logic for devIcon guessing
        devType = guess_type(
            device["devVendor"],
            device["devMac"],
            device["devLastIP"],
            device["devName"],
            default_type,
        )

        recordsToUpdate.append([devType, device["devMac"]])

    if len(recordsToUpdate) > 0:
        sql.executemany(
            "UPDATE Devices SET devType = ? WHERE devMac = ? ", recordsToUpdate
        )

    mylog("debug", "[Update Devices] Update devices end")


# -------------------------------------------------------------------------------
def save_scanned_devices(db):
    sql = db.sql  # TO-DO

    # Add Local MAC of default local interface
    local_mac_cmd = [
        "/sbin/ifconfig `ip -o route get 1 | sed 's/^.*dev \\([^ ]*\\).*$/\\1/;q'` | grep ether | awk '{print $2}'"
    ]
    local_mac = (
        subprocess.Popen(
            local_mac_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        .communicate()[0]
        .decode()
        .strip()
    )

    local_ip_cmd = ["ip -o route get 1 | sed 's/^.*src \\([^ ]*\\).*$/\\1/;q'"]
    local_ip = (
        subprocess.Popen(
            local_ip_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        .communicate()[0]
        .decode()
        .strip()
    )

    mylog("debug", ["[Save Devices] Saving this IP into the CurrentScan table:", local_ip])

    if check_IP_format(local_ip) == "":
        local_ip = "0.0.0.0"

    # Proceed if variable contains valid MAC
    if check_mac_or_internet(local_mac):
        sql.execute(
            f"""INSERT OR IGNORE INTO CurrentScan (cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod) VALUES ( '{local_mac}', '{local_ip}', Null, 'local_MAC') """
        )


# -------------------------------------------------------------------------------
def print_scan_stats(db):
    sql = db.sql  # TO-DO

    query = """
    SELECT
        (SELECT COUNT(*) FROM CurrentScan) AS devices_detected,
        (SELECT COUNT(*) FROM CurrentScan WHERE NOT EXISTS (SELECT 1 FROM Devices WHERE devMac = cur_MAC)) AS new_devices,
        (SELECT COUNT(*) FROM Devices WHERE devAlertDown != 0 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS down_alerts,
        (SELECT COUNT(*) FROM Devices WHERE devAlertDown != 0 AND devPresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS new_down_alerts,
        (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0) AS new_connections,
        (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS disconnections,
                (SELECT COUNT(*) FROM Devices, CurrentScan
                        WHERE devMac = cur_MAC
                            AND cur_IP IS NOT NULL
                            AND cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
                            AND cur_IP <> COALESCE(devPrimaryIPv4, '')
                            AND cur_IP <> COALESCE(devPrimaryIPv6, '')
                            AND cur_IP <> COALESCE(devLastIP, '')
                ) AS ip_changes,
        cur_ScanMethod,
        COUNT(*) AS scan_method_count
    FROM CurrentScan
    GROUP BY cur_ScanMethod
    """

    sql.execute(query)
    stats = sql.fetchall()

    mylog("verbose", f"[Scan Stats] Devices Detected.......: {stats[0]['devices_detected']}",)
    mylog("verbose", f"[Scan Stats] New Devices............: {stats[0]['new_devices']}")
    mylog("verbose", f"[Scan Stats] Down Alerts............: {stats[0]['down_alerts']}")
    mylog("verbose", f"[Scan Stats] New Down Alerts........: {stats[0]['new_down_alerts']}",)
    mylog("verbose", f"[Scan Stats] New Connections........: {stats[0]['new_connections']}",)
    mylog("verbose", f"[Scan Stats] Disconnections.........: {stats[0]['disconnections']}")
    mylog("verbose", f"[Scan Stats] IP Changes.............: {stats[0]['ip_changes']}")

    # if str(stats[0]["new_devices"]) != '0':
    mylog("trace", "   ================ DEVICES table content  ================")
    sql.execute("select * from Devices")
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog("trace", f"    {row_dict}")

    mylog("trace", "   ================ CurrentScan table content  ================")
    sql.execute("select * from CurrentScan")
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog("trace", f"    {row_dict}")

    mylog("trace", "   ================ Events table content where eve_PendingAlertEmail = 1  ================",)
    sql.execute("select * from Events where eve_PendingAlertEmail = 1")
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog("trace", f"    {row_dict}")

    mylog("trace", "   ================ Events table COUNT  ================")
    sql.execute("select count(*) from Events")
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog("trace", f"    {row_dict}")

    mylog("verbose", "[Scan Stats] Scan Method Statistics:")
    for row in stats:
        if row["cur_ScanMethod"] is not None:
            mylog("verbose", f"    {row['cur_ScanMethod']}: {row['scan_method_count']}")


# -------------------------------------------------------------------------------
def create_new_devices(db):
    sql = db.sql  # TO-DO
    startTime = timeNowDB()

    # Insert events for new devices from CurrentScan (not yet in Devices)

    mylog("debug", '[New Devices] Insert "New Device" Events')
    query_new_device_events = f"""
    INSERT INTO Events (
        eve_MAC, eve_IP, eve_DateTime,
        eve_EventType, eve_AdditionalInfo,
        eve_PendingAlertEmail
    )
    SELECT cur_MAC, cur_IP, '{startTime}', 'New Device', cur_Vendor, 1
    FROM CurrentScan
    WHERE NOT EXISTS (
        SELECT 1 FROM Devices
        WHERE devMac = cur_MAC
    )
    """

    # mylog('debug',f'[New Devices] Log Events Query: {query_new_device_events}')

    sql.execute(query_new_device_events)

    mylog("debug", "[New Devices] Insert Connection into session table")

    sql.execute(f"""INSERT INTO Sessions (
                        ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection,
                        ses_StillConnected, ses_AdditionalInfo
                    )
                    SELECT cur_MAC, cur_IP, 'Connected', '{startTime}', NULL, NULL, 1, cur_Vendor
                    FROM CurrentScan
                    WHERE EXISTS (
                        SELECT 1 FROM Devices
                        WHERE devMac = cur_MAC
                    )
                    AND NOT EXISTS (
                        SELECT 1 FROM Sessions
                        WHERE ses_MAC = cur_MAC AND ses_StillConnected = 1
                    )
                    """)

    # Create new devices from CurrentScan
    mylog("debug", "[New Devices] 2 Create devices")

    # default New Device values preparation
    newDevColumns = """devAlertEvents,
                        devAlertDown,
                        devPresentLastScan,
                        devIsArchived,
                        devIsNew,
                        devSkipRepeated,
                        devScan,
                        devOwner,
                        devFavorite,
                        devGroup,
                        devComments,
                        devLogEvents,
                        devLocation,
                        devCustomProps,
                        devParentRelType,
                        devReqNicsOnline
                        """

    newDevDefaults = f"""{safe_int("NEWDEV_devAlertEvents")},
                        {safe_int("NEWDEV_devAlertDown")},
                        {safe_int("NEWDEV_devPresentLastScan")},
                        {safe_int("NEWDEV_devIsArchived")},
                        {safe_int("NEWDEV_devIsNew")},
                        {safe_int("NEWDEV_devSkipRepeated")},
                        {safe_int("NEWDEV_devScan")},
                        '{sanitize_SQL_input(get_setting_value("NEWDEV_devOwner"))}',
                        {safe_int("NEWDEV_devFavorite")},
                        '{sanitize_SQL_input(get_setting_value("NEWDEV_devGroup"))}',
                        '{sanitize_SQL_input(get_setting_value("NEWDEV_devComments"))}',
                        {safe_int("NEWDEV_devLogEvents")},
                        '{sanitize_SQL_input(get_setting_value("NEWDEV_devLocation"))}',
                        '{sanitize_SQL_input(get_setting_value("NEWDEV_devCustomProps"))}',
                        '{sanitize_SQL_input(get_setting_value("NEWDEV_devParentRelType"))}',
                        {safe_int("NEWDEV_devReqNicsOnline")}
                        """

    # Fetch data from CurrentScan skipping ignored devices by IP and MAC
    query = """SELECT cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type
                FROM CurrentScan """

    mylog("debug", f"[New Devices] Collecting New Devices Query: {query}")
    current_scan_data = sql.execute(query).fetchall()

    for row in current_scan_data:
        (
            cur_MAC,
            cur_Name,
            cur_Vendor,
            cur_ScanMethod,
            cur_IP,
            cur_SyncHubNodeName,
            cur_NetworkNodeMAC,
            cur_PORT,
            cur_NetworkSite,
            cur_SSID,
            cur_Type,
        ) = row

        # Preserve raw values to determine source attribution
        raw_name = str(cur_Name).strip() if cur_Name else ""
        raw_vendor = str(cur_Vendor).strip() if cur_Vendor else ""
        raw_ip = str(cur_IP).strip() if cur_IP else ""
        raw_ssid = str(cur_SSID).strip() if cur_SSID else ""
        raw_parent_mac = cur_NetworkNodeMAC.strip() if cur_NetworkNodeMAC else ""
        raw_parent_port = str(cur_PORT).strip() if cur_PORT else ""

        # Handle NoneType
        cur_Name = raw_name if raw_name else "(unknown)"
        cur_Type = (
            str(cur_Type).strip() if cur_Type else get_setting_value("NEWDEV_devType")
        )
        cur_NetworkNodeMAC = raw_parent_mac
        cur_NetworkNodeMAC = (
            cur_NetworkNodeMAC
            if cur_NetworkNodeMAC and cur_MAC != "Internet"
            else (
                get_setting_value("NEWDEV_devParentMAC")
                if cur_MAC != "Internet"
                else "null"
            )
        )
        cur_SyncHubNodeName = (
            cur_SyncHubNodeName
            if cur_SyncHubNodeName and cur_SyncHubNodeName != "null"
            else (get_setting_value("SYNC_node_name"))
        )

        # Derive primary IP family values
        cur_IP = raw_ip
        cur_IP_normalized = check_IP_format(cur_IP) if ":" not in cur_IP else cur_IP

        # Validate IPv6 addresses using format_ip_long for consistency (do not store integer result)
        if cur_IP_normalized and ":" in cur_IP_normalized:
            validated_ipv6 = format_ip_long(cur_IP_normalized)
            if validated_ipv6 is None or validated_ipv6 < 0:
                cur_IP_normalized = ""

        primary_ipv4 = cur_IP_normalized if cur_IP_normalized and ":" not in cur_IP_normalized else ""
        primary_ipv6 = cur_IP_normalized if cur_IP_normalized and ":" in cur_IP_normalized else ""

        plugin_prefix = str(cur_ScanMethod).strip() if cur_ScanMethod else "NEWDEV"

        dev_mac_source = get_source_for_field_update_with_value(
            "devMac", plugin_prefix, cur_MAC, is_user_override=False
        )
        dev_name_source = get_source_for_field_update_with_value(
            "devName", plugin_prefix, raw_name, is_user_override=False
        )
        dev_vendor_source = get_source_for_field_update_with_value(
            "devVendor", plugin_prefix, raw_vendor, is_user_override=False
        )
        dev_last_ip_source = get_source_for_field_update_with_value(
            "devLastIP", plugin_prefix, cur_IP_normalized, is_user_override=False
        )
        dev_ssid_source = get_source_for_field_update_with_value(
            "devSSID", plugin_prefix, raw_ssid, is_user_override=False
        )
        dev_parent_mac_source = get_source_for_field_update_with_value(
            "devParentMAC", plugin_prefix, raw_parent_mac, is_user_override=False
        )
        dev_parent_port_source = get_source_for_field_update_with_value(
            "devParentPort", plugin_prefix, raw_parent_port, is_user_override=False
        )
        dev_parent_rel_type_source = "NEWDEV"
        dev_fqdn_source = "NEWDEV"
        dev_vlan_source = "NEWDEV"

        # Preparing the individual insert statement
        sqlQuery = f"""INSERT OR IGNORE INTO Devices
                        (
                            devMac,
                            devName,
                            devVendor,
                            devLastIP,
                            devPrimaryIPv4,
                            devPrimaryIPv6,
                            devFirstConnection,
                            devLastConnection,
                            devSyncHubNode,
                            devGUID,
                            devParentMAC,
                            devParentPort,
                            devSite,
                            devSSID,
                            devType,
                            devSourcePlugin,
                            devMacSource,
                            devNameSource,
                            devFqdnSource,
                            devLastIpSource,
                            devVendorSource,
                            devSsidSource,
                            devParentMacSource,
                            devParentPortSource,
                            devParentRelTypeSource,
                            devVlanSource,
                            {newDevColumns}
                        )
                        VALUES
                        (
                            '{sanitize_SQL_input(cur_MAC)}',
                            '{sanitize_SQL_input(cur_Name)}',
                            '{sanitize_SQL_input(cur_Vendor)}',
                            '{sanitize_SQL_input(cur_IP_normalized)}',
                            '{sanitize_SQL_input(primary_ipv4)}',
                            '{sanitize_SQL_input(primary_ipv6)}',
                            ?,
                            ?,
                            '{sanitize_SQL_input(cur_SyncHubNodeName)}',
                            {sql_generateGuid},
                            '{sanitize_SQL_input(cur_NetworkNodeMAC)}',
                            '{sanitize_SQL_input(cur_PORT)}',
                            '{sanitize_SQL_input(cur_NetworkSite)}',
                            '{sanitize_SQL_input(cur_SSID)}',
                            '{sanitize_SQL_input(cur_Type)}',
                            '{sanitize_SQL_input(cur_ScanMethod)}',
                            '{sanitize_SQL_input(dev_mac_source)}',
                            '{sanitize_SQL_input(dev_name_source)}',
                            '{sanitize_SQL_input(dev_fqdn_source)}',
                            '{sanitize_SQL_input(dev_last_ip_source)}',
                            '{sanitize_SQL_input(dev_vendor_source)}',
                            '{sanitize_SQL_input(dev_ssid_source)}',
                            '{sanitize_SQL_input(dev_parent_mac_source)}',
                            '{sanitize_SQL_input(dev_parent_port_source)}',
                            '{sanitize_SQL_input(dev_parent_rel_type_source)}',
                            '{sanitize_SQL_input(dev_vlan_source)}',
                            {newDevDefaults}
                        )"""

        mylog("trace", f"[New Devices] Create device SQL: {sqlQuery}")

        sql.execute(sqlQuery, (startTime, startTime))

    mylog("debug", "[New Devices] New Devices end")
    db.commitDB()


# -------------------------------------------------------------------------------
# Check if plugins data changed
def check_plugin_data_changed(pm, plugins_to_check):
    """
    Checks whether any of the specified plugins have updated data since their
    last recorded check time.

    This function compares each plugin's `lastDataChange` timestamp from
    `pm.plugin_states` with its corresponding `lastDataCheck` timestamp from
    `pm.plugin_checks`. If a plugin's data has changed more recently than it
    was last checked, it is flagged as changed.

    Args:
        pm (object): Plugin manager or state object containing:
            - plugin_states (dict): Per-plugin metadata with "lastDataChange".
            - plugin_checks (dict): Per-plugin last check timestamps.
        plugins_to_check (list[str]): List of plugin names to validate.

    Returns:
        bool: True if any plugin data has changed since last check,
              otherwise False.

    Logging:
        - Logs unexpected or invalid timestamps at level 'none'.
        - Logs when no changes are detected at level 'debug'.
        - Logs each changed plugin at level 'debug'.
    """

    plugins_changed = []

    for plugin_name in plugins_to_check:

        last_data_change = pm.plugin_states.get(plugin_name, {}).get("lastDataChange")
        last_data_check = pm.plugin_checks.get(plugin_name, "")

        if not last_data_change:
            continue

        # Normalize and validate last_changed timestamp
        last_changed_ts = normalizeTimeStamp(last_data_change)

        if last_changed_ts is None:
            mylog('none', f'[check_plugin_data_changed] Unexpected last_data_change timestamp for {plugin_name} (input|output): ({last_data_change}|{last_changed_ts})')

        # Normalize and validate last_data_check timestamp
        last_data_check_ts = normalizeTimeStamp(last_data_check)

        if last_data_check_ts is None:
            mylog('none', f'[check_plugin_data_changed] Unexpected last_data_check timestamp for {plugin_name} (input|output): ({last_data_check}|{last_data_check_ts})')

        # Track which plugins have newer state than last_checked
        if last_data_check_ts is None or last_changed_ts is None or last_changed_ts > last_data_check_ts:
            mylog('debug', f'[check_plugin_data_changed] {plugin_name} changed (last_changed_ts|last_data_check_ts): ({last_changed_ts}|{last_data_check_ts})')
            plugins_changed.append(plugin_name)

    # Skip if no plugin state changed since last check
    if len(plugins_changed) == 0:
        mylog('debug', f'[check_plugin_data_changed] No relevant plugin changes since last check for {plugins_to_check}')
        return False

    # Continue if changes detected
    for p in plugins_changed:
        mylog('debug', f'[check_plugin_data_changed] {p} changed (last_change|last_check): ({pm.plugin_states.get(p, {}).get("lastDataChange")}|{pm.plugin_checks.get(p)})')

    return True


# -------------------------------------------------------------------------------
def update_devices_names(pm):

    # --- Short-circuit if no name-resolution plugin has changed ---
    if check_plugin_data_changed(pm, ["DIGSCAN", "NSLOOKUP", "NBTSCAN", "AVAHISCAN"]) is False:
        mylog('debug', '[Update Device Name] No relevant plugin changes since last check.')
        return

    mylog('debug', '[Update Device Name] Check if unknown devices present to resolve names for or if REFRESH_FQDN enabled.')

    sql = pm.db.sql
    resolver = NameResolver(pm.db)
    device_handler = DeviceInstance()

    nameNotFound = "(name not found)"

    # Define resolution strategies in priority order
    strategies = [
        (resolver.resolve_dig, "DIGSCAN"),
        (resolver.resolve_mdns, "AVAHISCAN"),
        (resolver.resolve_nslookup, "NSLOOKUP"),
        (resolver.resolve_nbtlookup, "NBTSCAN"),
    ]

    def resolve_devices(devices, resolve_both_name_and_fqdn=True):
        """
        Attempts to resolve device names and/or FQDNs using available strategies.

        Parameters:
            devices (list): List of devices to resolve.
            resolve_both_name_and_fqdn (bool): If True, resolves both name and FQDN.
                                               If False, resolves only FQDN.

        Returns:
            recordsToUpdate (list): List of
                [newName, nameSource, newFQDN, fqdnSource, devMac] or [newFQDN, fqdnSource, devMac].
            recordsNotFound (list): List of [nameNotFound, devMac] for DB update.
            foundStats (dict): Number of successes per strategy.
            notFound (int): Number of devices not resolved.
        """
        recordsToUpdate = []
        recordsNotFound = []
        foundStats = {label: 0 for _, label in strategies}
        notFound = 0

        for device in devices:
            newName = nameNotFound
            newFQDN = ""

            # Attempt each resolution strategy in order
            for resolve_fn, label in strategies:
                resolved = resolve_fn(device["devMac"], device["devLastIP"])

                # Only use name if resolving both name and FQDN
                newName = resolved.cleaned if resolve_both_name_and_fqdn else None
                newFQDN = resolved.raw

                # If a valid result is found, record it and stop further attempts
                if (
                    newFQDN not in [nameNotFound, "", "localhost."] and " communications error to " not in newFQDN
                ):
                    foundStats[label] += 1

                    if resolve_both_name_and_fqdn:
                        recordsToUpdate.append([newName, label, newFQDN, label, device["devMac"]])
                    else:
                        recordsToUpdate.append([newFQDN, label, device["devMac"]])
                    break

            # If no name was resolved, queue device for "(name not found)" update
            if resolve_both_name_and_fqdn and newName == nameNotFound:
                notFound += 1
                if device["devName"] != nameNotFound:
                    recordsNotFound.append([nameNotFound, device["devMac"]])

        return recordsToUpdate, recordsNotFound, foundStats, notFound

    # --- Step 1: Update device names for unknown devices ---
    unknownDevices = device_handler.getUnknown()
    if unknownDevices:
        mylog("verbose", f"[Update Device Name] Trying to resolve devices without name. Unknown devices count: {len(unknownDevices)}",)

        # Try resolving both name and FQDN
        recordsToUpdate, recordsNotFound, fs, notFound = resolve_devices(
            unknownDevices
        )

        # Log summary
        res_string = f"{fs['DIGSCAN']}/{fs['AVAHISCAN']}/{fs['NSLOOKUP']}/{fs['NBTSCAN']}"
        mylog("verbose", f"[Update Device Name] Names Found (DIGSCAN/AVAHISCAN/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)} ({res_string})",)
        mylog("verbose", f"[Update Device Name] Names Not Found         : {notFound}")

        # Apply updates to database
        sql.executemany(
            """UPDATE Devices
                SET devName = CASE
                    WHEN COALESCE(devNameSource, '') IN ('USER', 'LOCKED') THEN devName
                    ELSE ?
                END
                WHERE devMac = ?
                  AND COALESCE(devNameSource, '') IN ('', 'NEWDEV')""",
            recordsNotFound,
        )

        records_by_plugin = {}
        for entry in recordsToUpdate:
            records_by_plugin.setdefault(entry[1], []).append(entry)

        for plugin_label, plugin_records in records_by_plugin.items():
            plugin_settings = get_plugin_authoritative_settings(plugin_label)
            name_clause = get_overwrite_sql_clause(
                "devName", "devNameSource", plugin_settings
            )
            fqdn_clause = get_overwrite_sql_clause(
                "devFQDN", "devFqdnSource", plugin_settings
            )

            sql.executemany(
                f"""UPDATE Devices
                    SET devName = CASE
                        WHEN {name_clause} THEN ?
                        ELSE devName
                    END,
                        devNameSource = CASE
                        WHEN {name_clause} THEN ?
                        ELSE devNameSource
                    END,
                        devFQDN = CASE
                        WHEN {fqdn_clause} THEN ?
                        ELSE devFQDN
                    END,
                        devFqdnSource = CASE
                        WHEN {fqdn_clause} THEN ?
                        ELSE devFqdnSource
                    END
                    WHERE devMac = ?""",
                plugin_records,
            )

    # --- Step 2: Optionally refresh FQDN for all devices ---
    if get_setting_value("REFRESH_FQDN"):
        allDevices = device_handler.getAll()
        if allDevices:
            mylog("verbose", f"[Update FQDN] Trying to resolve FQDN. Devices count: {len(allDevices)}",)

            # Try resolving only FQDN
            recordsToUpdate, _, fs, notFound = resolve_devices(
                allDevices, resolve_both_name_and_fqdn=False
            )

            # Log summary
            res_string = f"{fs['DIGSCAN']}/{fs['AVAHISCAN']}/{fs['NSLOOKUP']}/{fs['NBTSCAN']}"
            mylog("verbose", f"[Update FQDN] Names Found (DIGSCAN/AVAHISCAN/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)}({res_string})",)
            mylog("verbose", f"[Update FQDN] Names Not Found         : {notFound}")

            records_by_plugin = {}
            for entry in recordsToUpdate:
                records_by_plugin.setdefault(entry[1], []).append(entry)

            for plugin_label, plugin_records in records_by_plugin.items():
                plugin_settings = get_plugin_authoritative_settings(plugin_label)
                fqdn_clause = get_overwrite_sql_clause(
                    "devFQDN", "devFqdnSource", plugin_settings
                )

                # Apply FQDN-only updates
                sql.executemany(
                    f"""UPDATE Devices
                        SET devFQDN = CASE
                            WHEN {fqdn_clause} THEN ?
                            ELSE devFQDN
                        END,
                            devFqdnSource = CASE
                            WHEN {fqdn_clause} THEN ?
                            ELSE devFqdnSource
                        END
                        WHERE devMac = ?""",
                    plugin_records,
                )

    # Commit all database changes
    pm.db.commitDB()

    # --- Step 3: Log last checked time ---
    # After resolving names, update last checked
    pm.plugin_checks = {"DIGSCAN": timeNowDB(), "AVAHISCAN": timeNowDB(), "NSLOOKUP": timeNowDB(), "NBTSCAN": timeNowDB()}


# -------------------------------------------------------------------------------
# Updates devPresentLastScan for parent devices based on the presence of their NICs
def update_devPresentLastScan_based_on_nics(db):
    """
    Updates devPresentLastScan in the Devices table for parent devices
    based on the presence of their NICs and the devReqNicsOnline setting.

    Args:
        db: A database object with `.execute()` and `.fetchall()` methods.
    """

    sql = db.sql

    # Step 1: Load all devices from the DB
    devices = sql.execute("SELECT * FROM Devices").fetchall()

    # Convert rows to dicts (assumes sql.row_factory = sqlite3.Row or similar)
    devices = [dict(row) for row in devices]

    # Build MAC -> NICs map
    mac_to_nics = {}
    for device in devices:
        if device.get("devParentRelType") == "nic":
            parent_mac = device.get("devParentMAC")
            if parent_mac:
                mac_to_nics.setdefault(parent_mac, []).append(device)

    # Step 2: For each non-NIC device, determine new devPresentLastScan
    updates = []
    for device in devices:
        if device.get("devParentRelType") == "nic":
            continue  # skip NICs

        mac = device.get("devMac")
        if not mac:
            continue

        req_all = str(device.get("devReqNicsOnline")) == "1"
        nics = mac_to_nics.get(mac, [])

        original = device.get("devPresentLastScan", 0)
        new_present = original

        if nics:
            nic_statuses = [nic.get("devPresentLastScan") == 1 for nic in nics]
            if req_all:
                new_present = int(all(nic_statuses))
            else:
                new_present = int(any(nic_statuses))

        # Only add update if changed
        if original != new_present:
            updates.append((new_present, mac))

    # Step 3: Execute batch update
    for present, mac in updates:
        sql.execute(
            "UPDATE Devices SET devPresentLastScan = ? WHERE devMac = ?", (present, mac)
        )

    db.commitDB()
    return len(updates)


# -------------------------------------------------------------------------------
# Force devPresentLastScan based on devForceStatus
def update_devPresentLastScan_based_on_force_status(db):
    """
    Forces devPresentLastScan in the Devices table based on devForceStatus.

    devForceStatus values:
      - "online"  -> devPresentLastScan = 1
      - "offline" -> devPresentLastScan = 0
      - "dont_force" or empty -> no change

    Args:
        db: A database object with `.execute()` and `.fetchone()` methods.

    Returns:
        int: Number of devices updated.
    """

    sql = db.sql

    online_count_row = sql.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM Devices
        WHERE LOWER(COALESCE(devForceStatus, '')) = 'online'
          AND devPresentLastScan != 1
        """
    ).fetchone()
    online_updates = online_count_row["cnt"] if online_count_row else 0

    offline_count_row = sql.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM Devices
        WHERE LOWER(COALESCE(devForceStatus, '')) = 'offline'
          AND devPresentLastScan != 0
        """
    ).fetchone()
    offline_updates = offline_count_row["cnt"] if offline_count_row else 0

    if online_updates > 0:
        sql.execute(
            """
            UPDATE Devices
            SET devPresentLastScan = 1
            WHERE LOWER(COALESCE(devForceStatus, '')) = 'online'
            """
        )

    if offline_updates > 0:
        sql.execute(
            """
            UPDATE Devices
            SET devPresentLastScan = 0
            WHERE LOWER(COALESCE(devForceStatus, '')) = 'offline'
            """
        )

    total_updates = online_updates + offline_updates
    if total_updates > 0:
        mylog("debug", f"[Update Devices] Forced devPresentLastScan for {total_updates} devices")

    db.commitDB()
    return total_updates


# -------------------------------------------------------------------------------
# Check if the variable contains a valid MAC address or "Internet"
def check_mac_or_internet(input_str):
    # Regular expression pattern for matching a MAC address
    mac_pattern = r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})"

    if input_str.lower() == "internet":
        return True
    elif re.match(mac_pattern, input_str):
        return True
    else:
        return False


# -------------------------------------------------------------------------------
# Lookup unknown vendors on devices
def query_MAC_vendor(pMAC):
    pMACstr = str(pMAC)

    filePath = vendorsPath

    if os.path.isfile(vendorsPathNewest):
        filePath = vendorsPathNewest

    # Check MAC parameter
    mac = pMACstr.replace(":", "").lower()
    if len(pMACstr) != 17 or len(mac) != 12:
        return -2  # return -2 if ignored MAC

    # Search vendor in HW Vendors DB
    mac_start_string6 = mac[0:6]

    try:
        with open(filePath, "r") as f:
            for line in f:
                line_lower = (
                    line.lower()
                )  # Convert line to lowercase for case-insensitive matching
                if line_lower.startswith(mac_start_string6):
                    parts = line.split("\t", 1)
                    if len(parts) > 1:
                        vendor = parts[1].strip()
                        mylog("debug", [f"[Vendor Check] Found '{vendor}' for '{pMAC}' in {vendorsPath}"], )
                        return vendor
                    else:
                        mylog("debug", [f'[Vendor Check] ⚠ ERROR: Match found, but line could not be processed: "{line_lower}"'],)
                        return -1

        return -1  # MAC address not found in the database
    except FileNotFoundError:
        mylog("none", [f"[Vendor Check] ⚠ ERROR: Vendors file {vendorsPath} not found."])
        return -1
