#!/usr/bin/env python3
"""
Network device scanning and management module for NetAlertX.

This module handles device scanning, database operations, and device classification
for the NetAlertX system. It includes functions for excluding ignored devices,
saving scanned devices, generating scan statistics, creating and updating devices,
resolving device names, and guessing device icons and types based on various
attributes.

All database operations are (GOING TO BE) parameterized to prevent SQL injection, and input
validation is (GOING TO BE) enforced to enhance security. Logging is (GOING TO BE) used extensively for
debugging and monitoring.

Dependencies:
- Python standard libraries: sys, subprocess, os, re
- External modules: conf, helper, logger, const, models.device_instance, scan.name_resolution
- Temporary libraries: warnings(removable when all deprecations are able to be fully removed)
"""

import sys
import subprocess
import os
import re
import warnings
from typing import Optional, List, Tuple, Dict
from datetime import datetime

# Register NetAlertX directories
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

import conf
from helper import timeNowTZ, get_setting, get_setting_value, list_to_where, check_IP_format, sanitize_SQL_input
from logger import mylog
from const import vendorsPath, vendorsPathNewest, sql_generateGuid
from models.device_instance import DeviceInstance
from scan.name_resolution import NameResolver

# Base64 encoded HTML strings for FontAwesome icons, now with an extended icons dictionary for broader device coverage
ICONS = {
    "globe": "PGkgY2xhc3M9ImZhcyBmYS1nbG9iZSI+PC9pPg==",  # Internet or global network
    "phone": "PGkgY2xhc3M9ImZhcyBmYS1tb2JpbGUtYWx0Ij48L2k+",  # Smartphone
    "laptop": "PGkgY2xhc3M9ImZhIGZhLWxhcHRvcCI+PC9pPg==",  # Laptop
    "printer": "PGkgY2xhc3M9ImZhIGZhLXByaW50ZXIiPjwvaT4=",  # Printer
    "router": "PGkgY2xhc3M9ImZhcyBmYS1yYW5kb20iPjwvaT4=",  # Router or network switch
    "tv": "PGkgY2xhc3M9ImZhIGZhLXR2Ij48L2k+",  # Television
    "desktop": "PGkgY2xhc3M9ImZhIGZhLWRlc2t0b3AiPjwvaT4=",  # Desktop PC
    "tablet": "PGkgY2xhc3M9ImZhIGZhLXRhYmxldCI+PC9pPg==",  # Tablet
    "watch": "PGkgY2xhc3M9ImZhcyBmYS1jbG9jayI+PC9pPg==",  # Fallback to clock since smartwatch is nonfree in FontAwesome
    "camera": "PGkgY2xhc3M9ImZhIGZhLWNhbWVyYSI+PC9pPg==",  # Camera or webcam
    "home": "PGkgY2xhc3M9ImZhIGZhLWhvbWUiPjwvaT4=",  # Smart home device
    "apple": "PGkgY2xhc3M9ImZhYiBmYS1hcHBsZSI+PC9pPg==",  # Apple device
    "ethernet": "PGkgY2xhc3M9ImZhcyBmYS1uZXR3b3JrLXdpcmVkIj48L2k+",  # Free alternative for ethernet icon in FontAwesome
    "google": "PGkgY2xhc3M9ImZhYiBmYS1nb29nbGUiPjwvaT4=",  # Google device
    "raspberry": "PGkgY2xhc3M9ImZhYiBmYS1yYXNwYmVycnktcGkiPjwvaT4=",  # Raspberry Pi
    "microchip": "PGkgY2xhc3M9ImZhcyBmYS1taWNyb2NoaXAiPjwvaT4=",  # IoT or embedded device
    "server": "PGkgY2xhc3M9ImZhcyBmYS1zZXJ2ZXIiPjwvaT4=",  # Server
    "gamepad": "PGkgY2xhc3M9ImZhcyBmYS1nYW1lcGFkIj48L2k+",  # Gaming console
    "lightbulb": "PGkgY2xhc3M9ImZhcyBmYS1saWdodGJ1bGIiPjwvaT4=",  # Smart light
    "speaker": "PGkgY2xhc3M9ImZhcyBmYS12b2x1bWUtdXAiPjwvaT4=",  # Free speaker alt icon for smart speakers in FontAwesome
    "lock": "PGkgY2xhc3M9ImZhcyBmYS1sb2NrIj48L2k+",  # Security device
}

# Extended device types for comprehensive classification
DEVICE_TYPES = {
    "Internet": "Internet Gateway",
    "Phone": "Smartphone",
    "Laptop": "Laptop",
    "Printer": "Printer",
    "Router": "Router",
    "TV": "Television",
    "Desktop": "Desktop PC",
    "Tablet": "Tablet",
    "Smartwatch": "Smartwatch",
    "Camera": "Camera",
    "SmartHome": "Smart Home Device",
    "Server": "Server",
    "GamingConsole": "Gaming Console",
    "IoT": "IoT Device",
    "NetworkSwitch": "Network Switch",
    "AccessPoint": "Access Point",
    "SmartLight": "Smart Light",
    "SmartSpeaker": "Smart Speaker",
    "SecurityDevice": "Security Device",
    "Unknown": "Unknown Device",
}

# Remove devices from CurrentScan table that match ignored MAC or IP addresses.
def exclude_ignored_devices(db) -> None:
    """
    Remove devices from CurrentScan table that match ignored MAC or IP addresses.

    Args:
        db: Database connection object with SQL interface.
    """
    try:
        mac_conditions = list_to_where('OR', 'cur_MAC', 'LIKE', get_setting_value('NEWDEV_ignored_MACs'))
        ip_conditions = list_to_where('OR', 'cur_IP', 'LIKE', get_setting_value('NEWDEV_ignored_IPs'))
        
        conditions = [cond for cond in [mac_conditions, ip_conditions] if cond]
        if not conditions:
            mylog('debug', '[New Devices] No ignored MACs or IPs to exclude.')
            return
        
        query = "DELETE FROM CurrentScan WHERE " + " OR ".join(f"({cond})" for cond in conditions)
        mylog('debug', f'[New Devices] Excluding Ignored Devices Query: {query}')
        
        db.sql.execute(query)
        db.commitDB()
    except Exception as e:
        mylog('error', f'[New Devices] Error excluding ignored devices: {str(e)}')

# Save scanned devices to the CurrentScan table, including local device info.
def save_scanned_devices(db) -> None:
    """
    Save scanned devices to the CurrentScan table, including local device info.

    Args:
        db: Database connection object with SQL interface.
    """
    try:
        # Get local MAC and IP using safer subprocess calls
        local_mac_cmd = ["bash", "-c", "ip link show $(ip -o route get 1 | awk '{print $5}') | grep ether | awk '{print $2}'"]
        local_ip_cmd = ["bash", "-c", "ip -o route get 1 | awk '{print $7}'"]
        
        try:
            local_mac = subprocess.check_output(local_mac_cmd, text=True, stderr=subprocess.STDOUT).strip()
            local_ip = subprocess.check_output(local_ip_cmd, text=True, stderr=subprocess.STDOUT).strip()
        except subprocess.CalledProcessError as e:
            mylog('error', f'[Save Devices] Error getting local MAC/IP: {str(e)}')
            local_mac = ""
            local_ip = "0.0.0.0"
        
        mylog('debug', f'[Save Devices] Saving IP: {local_ip}, MAC: {local_mac}')
        
        if not check_IP_format(local_ip):
            local_ip = '0.0.0.0'
        
        if check_mac_or_internet(local_mac):
            query = """
                INSERT OR IGNORE INTO CurrentScan (cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod)
                VALUES (?, ?, NULL, 'local_MAC')
            """
            db.sql.execute(query, (local_mac, local_ip))
            db.commitDB()
        else:
            mylog('warning', f'[Save Devices] Invalid MAC address: {local_mac}')
    except Exception as e:
        mylog('error', f'[Save Devices] Error saving scanned devices: {str(e)}')

# Generate and log statistics about the current network scan.
def print_scan_stats(db) -> None:
    """
    Generate and log statistics about the current network scan.

    Args:
        db: Database connection object with SQL interface.
    """
    try:
        query = """
            SELECT
                (SELECT COUNT(*) FROM CurrentScan) AS devices_detected,
                (SELECT COUNT(*) FROM CurrentScan WHERE NOT EXISTS (SELECT 1 FROM Devices WHERE devMac = cur_MAC)) AS new_devices,
                (SELECT COUNT(*) FROM Devices WHERE devAlertDown != 0 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS down_alerts,
                (SELECT COUNT(*) FROM Devices WHERE devAlertDown != 0 AND devPresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS new_down_alerts,
                (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0) AS new_connections,
                (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS disconnections,
                (SELECT COUNT(*) FROM Devices, CurrentScan WHERE devMac = cur_MAC AND devLastIP <> cur_IP) AS ip_changes,
                cur_ScanMethod,
                COUNT(*) AS scan_method_count
            FROM CurrentScan
            GROUP BY cur_ScanMethod
        """
        
        db.sql.execute(query)
        stats = db.sql.fetchall()
        
        if not stats:
            mylog('verbose', '[Scan Stats] No scan statistics available.')
            return
        
        mylog('verbose', f'[Scan Stats] Devices Detected.......: {stats[0]["devices_detected"]}')
        mylog('verbose', f'[Scan Stats] New Devices............: {stats[0]["new_devices"]}')
        mylog('verbose', f'[Scan Stats] Down Alerts............: {stats[0]["down_alerts"]}')
        mylog('verbose', f'[Scan Stats] New Down Alerts........: {stats[0]["new_down_alerts"]}')
        mylog('verbose', f'[Scan Stats] New Connections........: {stats[0]["new_connections"]}')
        mylog('verbose', f'[Scan Stats] Disconnections.........: {stats[0]["disconnections"]}')
        mylog('verbose', f'[Scan Stats] IP Changes.............: {stats[0]["ip_changes"]}')
        
        # Detailed table dumps for debugging
        for table, query in [
            ("Devices", "SELECT * FROM Devices"),
            ("CurrentScan", "SELECT * FROM CurrentScan"),
            ("Events (Pending Alerts)", "SELECT * FROM Events WHERE eve_PendingAlertEmail = 1"),
            ("Events (Count)", "SELECT COUNT(*) AS event_count FROM Events")
        ]:
            mylog('trace', f'   ================ {table} content ================')
            db.sql.execute(query)
            for row in db.sql.fetchall():
                mylog('trace', f'    {dict(row)}')
        
        mylog('verbose', '[Scan Stats] Scan Method Statistics:')
        for row in stats:
            if row["cur_ScanMethod"]:
                mylog('verbose', f'    {row["cur_ScanMethod"]}: {row["scan_method_count"]}')
    except Exception as e:
        mylog('error', f'[Scan Stats] Error generating scan statistics: {str(e)}')


# Create new device records in the Devices table from CurrentScan data.
def create_new_devices(db) -> None:
    """
    Create new device records in the Devices table from CurrentScan data.

    Args:
        db: Database connection object with SQL interface.
    """
    try:
        start_time = timeNowTZ()
        mylog('debug', '[New Devices] Creating new devices')
        
        # Insert events for new devices using parameterized query
        event_query = """
            INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime, eve_EventType, eve_AdditionalInfo, eve_PendingAlertEmail)
            SELECT cur_MAC, cur_IP, ?, 'New Device', cur_Vendor, 1
            FROM CurrentScan
            WHERE NOT EXISTS (SELECT 1 FROM Devices WHERE devMac = cur_MAC)
        """
        db.sql.execute(event_query, (start_time,))
        mylog('debug', '[New Devices] Logged new device events')
        
        # Insert new sessions using parameterized query
        session_query = """
            INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                                 ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo)
            SELECT cur_MAC, cur_IP, 'Connected', ?, NULL, NULL, 1, cur_Vendor
            FROM CurrentScan
            WHERE NOT EXISTS (SELECT 1 FROM Sessions WHERE ses_MAC = cur_MAC)
        """
        db.sql.execute(session_query, (start_time,))
        mylog('debug', '[New Devices] Inserted new sessions')
        
        # Prepare default device attributes
        new_dev_columns = [
            "devAlertEvents", "devAlertDown", "devPresentLastScan", "devIsArchived", "devIsNew",
            "devSkipRepeated", "devScan", "devOwner", "devFavorite", "devGroup",
            "devComments", "devLogEvents", "devLocation", "devCustomProps"
        ]
        new_dev_values = [
            get_setting_value('NEWDEV_devAlertEvents'),
            get_setting_value('NEWDEV_devAlertDown'),
            get_setting_value('NEWDEV_devPresentLastScan'),
            get_setting_value('NEWDEV_devIsArchived'),
            get_setting_value('NEWDEV_devIsNew'),
            get_setting_value('NEWDEV_devSkipRepeated'),
            get_setting_value('NEWDEV_devScan'),
            sanitize_SQL_input(get_setting_value('NEWDEV_devOwner')),
            get_setting_value('NEWDEV_devFavorite'),
            sanitize_SQL_input(get_setting_value('NEWDEV_devGroup')),
            sanitize_SQL_input(get_setting_value('NEWDEV_devComments')),
            get_setting_value('NEWDEV_devLogEvents'),
            sanitize_SQL_input(get_setting_value('NEWDEV_devLocation')),
            sanitize_SQL_input(get_setting_value('NEWDEV_devCustomProps')),
        ]
        
        # Fetch CurrentScan data
        query = """
            SELECT cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName,
                   cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type
            FROM CurrentScan
        """
        db.sql.execute(query)
        current_scan_data = db.sql.fetchall()
        
        for row in current_scan_data:
            cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName, \
            cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type = row
            
            # Sanitize and handle None values
            cur_Name = cur_Name.strip() if cur_Name else '(unknown)'
            cur_Type = cur_Type.strip() if cur_Type else get_setting_value("NEWDEV_devType")
            cur_NetworkNodeMAC = cur_NetworkNodeMAC.strip() if cur_NetworkNodeMAC else ''
            cur_NetworkNodeMAC = cur_NetworkNodeMAC if cur_NetworkNodeMAC and cur_MAC != "Internet" else \
                                 (get_setting_value("NEWDEV_devParentMAC") if cur_MAC != "Internet" else "null")
            cur_SyncHubNodeName = cur_SyncHubNodeName if cur_SyncHubNodeName and cur_SyncHubNodeName != "null" else \
                                  get_setting_value("SYNC_node_name")
            
            # Parameterized insert query
            insert_query = f"""
                INSERT OR IGNORE INTO Devices (
                    devMac, devName, devVendor, devLastIP, devFirstConnection, devLastConnection,
                    devSyncHubNode, devGUID, devParentMAC, devParentPort, devSite, devSSID,
                    devType, devSourcePlugin, {', '.join(new_dev_columns)}
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, {sql_generateGuid}, ?, ?, ?, ?, ?, ?, {', '.join('?' for _ in new_dev_columns)}
                )
            """
            params = [
                sanitize_SQL_input(cur_MAC), sanitize_SQL_input(cur_Name), sanitize_SQL_input(cur_Vendor),
                sanitize_SQL_input(cur_IP), start_time, start_time, sanitize_SQL_input(cur_SyncHubNodeName),
                sanitize_SQL_input(cur_NetworkNodeMAC), sanitize_SQL_input(cur_PORT),
                sanitize_SQL_input(cur_NetworkSite), sanitize_SQL_input(cur_SSID), sanitize_SQL_input(cur_Type),
                sanitize_SQL_input(cur_ScanMethod)
            ] + new_dev_values
            
            mylog('trace', f'[New Devices] Create device SQL: {insert_query % tuple("?" for _ in params)}')
            db.sql.execute(insert_query, params)
        
        db.commitDB()
        mylog('debug', '[New Devices] New devices created successfully')
    except Exception as e:
        mylog('error', f'[New Devices] Error creating new devices: {str(e)}')
        db.rollbackDB()


# Update device data in the Devices table based on CurrentScan data.
def update_devices_data_from_scan(db) -> None:
    """
    Update device data in the Devices table based on CurrentScan data.

    Args:
        db: Database connection object with SQL interface.
    """
    try:
        start_time = timeNowTZ().strftime('%Y-%m-%d %H:%M:%S')
        mylog('debug', '[Update Devices] Updating device data')
        
        # Update last connection and presence
        db.sql.execute("""
            UPDATE Devices
            SET devLastConnection = ?, devPresentLastScan = 1
            WHERE devPresentLastScan = 0
              AND EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)
        """, (start_time,))
        
        # Clear presence for inactive devices
        db.sql.execute("""
            UPDATE Devices
            SET devPresentLastScan = 0
            WHERE NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)
        """)
        
        # Update fields conditionally using parameterized subqueries
        update_queries = [
            ("devLastIP", "cur_IP", None),
            ("devVendor", "cur_Vendor", "devVendor IS NULL OR devVendor IN ('', 'null', '(unknown)', '(Unknown)')"),
            ("devParentPort", "cur_PORT", "devParentPort IS NULL OR devParentPort IN ('', 'null', '(unknown)', '(Unknown)') AND (SELECT cur_PORT FROM CurrentScan WHERE devMac = cur_MAC) NOT IN ('', 'null')"),
            ("devParentMAC", "cur_NetworkNodeMAC", "devParentMAC IS NULL OR devParentMAC IN ('', 'null', '(unknown)', '(Unknown)') AND (SELECT cur_NetworkNodeMAC FROM CurrentScan WHERE devMac = cur_MAC) NOT IN ('', 'null')"),
            ("devSite", "cur_NetworkSite", "devSite IS NULL OR devSite IN ('', 'null') AND (SELECT cur_NetworkSite FROM CurrentScan WHERE devMac = cur_MAC) NOT IN ('', 'null')"),
            ("devSSID", "cur_SSID", "devSSID IS NULL OR devSSID IN ('', 'null') AND (SELECT cur_SSID FROM CurrentScan WHERE devMac = cur_MAC) NOT IN ('', 'null')"),
            ("devType", "cur_Type", "devType IS NULL OR devType IN ('', 'null') AND (SELECT cur_Type FROM CurrentScan WHERE devMac = cur_MAC) NOT IN ('', 'null')"),
            ("devName", "cur_Name", "devName IN ('(unknown)', '(name not found)', '') OR devName IS NULL AND (SELECT cur_Name FROM CurrentScan WHERE devMac = cur_MAC) NOT IN ('', 'null')"),
        ]
        
        for field, source, condition in update_queries:
            query = f"""
                UPDATE Devices
                SET {field} = (SELECT {source} FROM CurrentScan WHERE devMac = cur_MAC)
                WHERE EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)
                {f'AND {condition}' if condition else ''}
            """
            db.sql.execute(query)
            mylog('debug', f'[Update Devices] Updated {field}')
        
        # Update vendors for unknown devices
        vendor_records = []
        for device in db.sql.execute("SELECT devMac FROM Devices WHERE devVendor IS NULL OR devVendor IN ('', 'null', '(unknown)', '(Unknown)')"):
            vendor = query_MAC_vendor(device['devMac'])
            if vendor not in ("-1", "-2"):
                vendor_records.append((vendor, device['devMac']))
        
        if vendor_records:
            db.sql.executemany("UPDATE Devices SET devVendor = ? WHERE devMac = ?", vendor_records)
            mylog('debug', f'[Update Devices] Updated {len(vendor_records)} vendor records')
        
        # Update icons
        default_icon = get_setting_value('NEWDEV_devIcon')
        icon_query = """
            SELECT devMac, devVendor, devLastIP, devName
            FROM Devices
            WHERE devIcon IN ('', 'null'{extra}) OR devIcon IS NULL
        """.format(extra=f", '{default_icon}'" if get_setting_value('NEWDEV_replace_preset_icon') else '')
        
        icon_records = [
            (guess_icon(row['devVendor'], row['devMac'], row['devLastIP'], row['devName'], default_icon), row['devMac'])
            for row in db.sql.execute(icon_query)
        ]
        
        if icon_records:
            db.sql.executemany("UPDATE Devices SET devIcon = ? WHERE devMac = ?", icon_records)
            mylog('debug', f'[Update Devices] Updated {len(icon_records)} icon records')
        
        # Update types
        default_type = get_setting_value('NEWDEV_devType')
        type_records = [
            (guess_type(row['devVendor'], row['devMac'], row['devLastIP'], row['devName'], default_type), row['devMac'])
            for row in db.sql.execute("SELECT devMac, devVendor, devLastIP, devName FROM Devices WHERE devType IN ('', 'null') OR devType IS NULL")
        ]
        
        if type_records:
            db.sql.executemany("UPDATE Devices SET devType = ? WHERE devMac = ?", type_records)
            mylog('debug', f'[Update Devices] Updated {len(type_records)} type records')
        
        db.commitDB()
        mylog('debug', '[Update Devices] Device data updated successfully')
    except Exception as e:
        mylog('error', f'[Update Devices] Error updating device data: {str(e)}')
        db.rollbackDB()

# Update the names for devices in the database
def update_devices_names(db) -> None:
    """
    Update device names and FQDNs using various resolution strategies.

    Args:
        db: Database connection object with SQL interface.
    """
    try:
        resolver = NameResolver(db)
        device_handler = DeviceInstance(db)
        name_not_found = "(name not found)"
        
        strategies = [
            (resolver.resolve_dig, 'dig'),
            (resolver.resolve_mdns, 'mdns'),
            (resolver.resolve_nslookup, 'nslookup'),
            (resolver.resolve_nbtlookup, 'nbtlookup')
        ]
        
        def resolve_devices(devices: List[Dict], resolve_both_name_and_fqdn: bool = True) -> Tuple[List, List, Dict, int]:
            """
            Resolve device names and/or FQDNs using available strategies.

            Args:
                devices: List of devices to resolve.
                resolve_both_name_and_fqdn: If True, resolve both name and FQDN; else, resolve only FQDN.

            Returns:
                Tuple of (records_to_update, records_not_found, found_stats, not_found_count).
            """
            records_to_update = []
            records_not_found = []
            found_stats = {label: 0 for _, label in strategies}
            not_found = 0
            
            for device in devices:
                new_name = name_not_found if resolve_both_name_and_fqdn else None
                new_fqdn = ''
                
                for resolve_fn, label in strategies:
                    try:
                        resolved = resolve_fn(device['devMac'], device['devLastIP'])
                        new_name = resolved.cleaned if resolve_both_name_and_fqdn else None
                        new_fqdn = resolved.raw
                        
                        if new_fqdn and new_fqdn not in [name_not_found, '', 'localhost.'] and ' communications error to ' not in new_fqdn:
                            found_stats[label] += 1
                            records_to_update.append([new_name, new_fqdn, device['devMac']] if resolve_both_name_and_fqdn else [new_fqdn, device['devMac']])
                            break
                    except Exception as e:
                        mylog('debug', f'[Update Device Name] Error in {label} resolution for {device["devMac"]}: {str(e)}')
                
                if resolve_both_name_and_fqdn and new_name == name_not_found and device['devName'] != name_not_found:
                    not_found += 1
                    records_not_found.append([name_not_found, device['devMac']])
            
            return records_to_update, records_not_found, found_stats, not_found
        
        # Update unknown device names
        unknown_devices = device_handler.getUnknown()
        if unknown_devices:
            mylog('verbose', f'[Update Device Name] Resolving {len(unknown_devices)} unknown devices')
            records_to_update, records_not_found, found_stats, not_found = resolve_devices(unknown_devices)
            
            mylog('verbose', f"[Update Device Name] Names Found (DiG/mDNS/NSLOOKUP/NBTSCAN): {len(records_to_update)} "
                             f"({found_stats['dig']}/{found_stats['mdns']}/{found_stats['nslookup']}/{found_stats['nbtlookup']})")
            mylog('verbose', f'[Update Device Name] Names Not Found: {not_found}')
            
            if records_not_found:
                db.sql.executemany("UPDATE Devices SET devName = ? WHERE devMac = ?", records_not_found)
            if records_to_update:
                db.sql.executemany("UPDATE Devices SET devName = ?, devFQDN = ? WHERE devMac = ?", records_to_update)
        
        # Optionally refresh FQDNs
        if get_setting_value("REFRESH_FQDN"):
            all_devices = device_handler.getAll()
            if all_devices:
                mylog('verbose', f'[Update FQDN] Resolving FQDN for {len(all_devices)} devices')
                records_to_update, _, found_stats, not_found = resolve_devices(all_devices, resolve_both_name_and_fqdn=False)
                
                mylog('verbose', f"[Update FQDN] Names Found (DiG/mDNS/NSLOOKUP/NBTSCAN): {len(records_to_update)} "
                                 f"({found_stats['dig']}/{found_stats['mdns']}/{found_stats['nslookup']}/{found_stats['nbtlookup']})")
                mylog('verbose', f'[Update FQDN] Names Not Found: {not_found}')
                
                if records_to_update:
                    db.sql.executemany("UPDATE Devices SET devFQDN = ? WHERE devMac = ?", records_to_update)
        
        db.commitDB()
        mylog('debug', '[Update Device Names] Device names updated successfully')
    except Exception as e:
        mylog('error', f'[Update Device Names] Error updating device names: {str(e)}')
        db.rollbackDB()

# Check if the argument contains a valid MAC address or "Internet", otherwise return False
def check_mac_or_internet(input_str: Optional[str]) -> bool:
    """
    Validate if the input string is a valid MAC address or 'Internet'.

    Args:
        input_str: The string to validate (MAC address or 'Internet').

    Returns:
        bool: True if valid MAC address or 'Internet', False otherwise.
    """
    if not input_str:
        return False

    input_str = input_str.strip().lower()
    if input_str == 'internet':
        return True

    # MAC address pattern: 12 hexadecimal digits in groups of 2, separated by : or -
    mac_pattern = r'^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$'
    return bool(re.match(mac_pattern, input_str))

# Lookup unknown vendors on devices
def query_MAC_vendor(pMAC: Optional[str] = None) -> str:
    """
    Look up the vendor for a given MAC address in the vendors database.

    Args:
        pMAC: The MAC address to query.

    Returns:
        str: Vendor name if found, -1 if not found, -2 if invalid MAC.
    """
    if not pMAC or len(pMAC.replace(':', '').strip()) != 12:
        mylog('debug', f"[Vendor Check] Invalid MAC address: '{pMAC}'")
        return "-2"

    file_path = vendorsPathNewest if os.path.isfile(vendorsPathNewest) else vendorsPath
    mac = pMAC.replace(':', '').lower()[:9]  # Check first 9 characters (OUI or extended OUI)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.lower().startswith(mac[:6]) or line.lower().startswith(mac):
                    parts = line.split('\t', 1)
                    if len(parts) > 1:
                        vendor = parts[1].strip()
                        mylog('debug', f"[Vendor Check] Found '{vendor}' for '{pMAC}' in {file_path}")
                        return vendor
        mylog('debug', f"[Vendor Check] No vendor found for '{pMAC}'")
        return "-1"
    except FileNotFoundError:
        mylog('error', f"[Vendor Check] Vendors file {file_path} not found.")
        return "-1"
    except Exception as e:
        mylog('error', f"[Vendor Check] Error reading vendors file: {str(e)}")
        return "-1"

# Guess device attributes such as type of device and associated device icon
def guess_device_attributes(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default_icon: str,
    default_type: str
    ) -> Tuple[str, str]:
    """
    Guess the appropriate FontAwesome icon and device type based on device attributes.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default_icon: Default icon to return if no match is found.
        default_type: Default type to return if no match is found.

    Returns:
        Tuple[str, str]: A tuple containing the guessed icon (Base64-encoded HTML string)
                         and the guessed device type (string).
    """
    mylog('debug', f"[guess_device_attributes] Guessing attributes for (vendor|mac|ip|name): ('{vendor}'|'{mac}'|'{ip}'|'{name}')")
    # Normalize inputs
    vendor = str(vendor).lower().strip() if vendor else "unknown"
    mac = str(mac).upper().strip() if mac else "00:00:00:00:00:00"
    ip = str(ip).strip() if ip else "169.254.0.0"  # APIPA address for unknown IPs per RFC 3927
    name = str(name).lower().strip() if name else "(unknown)"

    # --- Icon Guessing Logic ---
    if mac == "INTERNET":
        icon = ICONS.get("globe", default_icon)
    else:
        # Vendor-based icon guessing
        icon_vendor_patterns = {
            "apple": "apple",
            "samsung|motorola|xiaomi|huawei": "phone",
            "dell|lenovo|asus|acer": "laptop",
            "hp|epson|canon|brother": "printer",
            "cisco|ubiquiti|netgear|tp-link|d-link|mikrotik": "router",
            "lg|samsung electronics|sony|vizio": "tv",
            "raspberry pi": "raspberry",
            "google": "google",
            "espressif|particle": "microchip",
            "intel|amd": "desktop",
            "amazon": "speaker",
            "philips hue|lifx": "lightbulb",
            "aruba|meraki": "ethernet",
            "qnap|synology": "server",
            "nintendo|sony interactive|microsoft": "gamepad",
            "ring|blink|arlo": "camera",
            "nest": "home",
        }
        for pattern, icon_key in icon_vendor_patterns.items():
            if re.search(pattern, vendor, re.IGNORECASE):
                icon = ICONS.get(icon_key, default_icon)
                break
        else:
            # MAC-based icon guessing
            mac_clean = mac.replace(':', '').replace('-', '').upper()
            icon_mac_patterns = {
                "001A79|B0BE83|BC926B": "apple",
                "001B63|BC4C4C": "tablet",
                "74ACB9|002468": "ethernet",
                "B827EB": "raspberry",
                "001422|001874": "desktop",
                "001CBF|002186": "server",
            }
            for pattern_str, icon_key in icon_mac_patterns.items():
                patterns = [p.replace(':', '').replace('-', '').upper() for p in pattern_str.split('|')]
                if any(mac_clean.startswith(p) for p in patterns):
                    icon = ICONS.get(icon_key, default_icon)
                    break
            else:
                # Name-based icon guessing
                icon_name_patterns = {
                    "iphone|ipad|macbook|imac": "apple",
                    "pixel|galaxy|redmi": "phone",
                    "laptop|notebook": "laptop",
                    "printer|print": "printer",
                    "router|gateway|ap|access[ -]?point": "router",
                    "tv|television|smarttv": "tv",
                    "desktop|pc|computer": "desktop",
                    "tablet|pad": "tablet",
                    "watch|wear": "watch",
                    "camera|cam|webcam": "camera",
                    "echo|alexa|dot": "speaker",
                    "hue|lifx|bulb": "lightbulb",
                    "server|nas": "server",
                    "playstation|xbox|switch": "gamepad",
                    "raspberry|pi": "raspberry",
                    "google|chromecast|nest": "google",
                    "doorbell|lock|security": "lock",
                }
                for pattern, icon_key in icon_name_patterns.items():
                    if re.search(pattern, name, re.IGNORECASE):
                        icon = ICONS.get(icon_key, default_icon)
                        break
                else:
                    # IP-based icon guessing
                    icon_ip_patterns = {
                        r"^192\.168\.[0-1]\.1$": "router",
                        r"^10\.0\.0\.1$": "router",
                        r"^192\.168\.[0-1]\.[2-9]$": "desktop",
                        r"^192\.168\.[0-1]\.1\d{2}$": "phone",
                    }
                    for pattern, icon_key in icon_ip_patterns.items():
                        if re.match(pattern, ip):
                            icon = ICONS.get(icon_key, default_icon)
                            break
                    else:
                        icon = default_icon

    # --- Type Guessing Logic ---
    if mac == "INTERNET":
        type_ = DEVICE_TYPES.get("Internet", default_type)
    else:
        # Vendor-based type guessing
        type_vendor_patterns = {
            "apple|samsung|motorola|xiaomi|huawei": "Phone",
            "dell|lenovo|asus|acer|hp": "Laptop",
            "epson|canon|brother": "Printer",
            "cisco|ubiquiti|netgear|tp-link|d-link|mikrotik|aruba|meraki": "Router",
            "lg|samsung electronics|sony|vizio": "TV",
            "raspberry pi": "IoT",
            "google|nest": "SmartHome",
            "espressif|particle": "IoT",
            "intel|amd": "Desktop",
            "amazon": "SmartSpeaker",
            "philips hue|lifx": "SmartLight",
            "qnap|synology": "Server",
            "nintendo|sony interactive|microsoft": "GamingConsole",
            "ring|blink|arlo": "Camera",
        }
        for pattern, type_key in type_vendor_patterns.items():
            if re.search(pattern, vendor, re.IGNORECASE):
                type_ = DEVICE_TYPES.get(type_key, default_type)
                break
        else:
            # MAC-based type guessing
            mac_clean = mac.replace(':', '').replace('-', '').upper()
            type_mac_patterns = {
                "00:1A:79|B0:BE:83|BC:92:6B": "Phone",
                "00:1B:63|BC:4C:4C": "Tablet",
                "74:AC:B9|00:24:68": "AccessPoint",
                "B8:27:EB": "IoT",
                "00:14:22|00:18:74": "Desktop",
                "00:1C:BF|00:21:86": "Server",
            }
            for pattern_str, type_key in type_mac_patterns.items():
                patterns = [p.replace(':', '').replace('-', '').upper() for p in pattern_str.split('|')]
                if any(mac_clean.startswith(p) for p in patterns):
                    type_ = DEVICE_TYPES.get(type_key, default_type)
                    break
            else:
                # Name-based type guessing
                type_name_patterns = {
                    "iphone|ipad": "Phone",
                    "macbook|imac": "Laptop",
                    "pixel|galaxy|redmi": "Phone",
                    "laptop|notebook": "Laptop",
                    "printer|print": "Printer",
                    "router|gateway|ap|access[ -]?point": "Router",
                    "tv|television|smarttv": "TV",
                    "desktop|pc|computer": "Desktop",
                    "tablet|pad": "Tablet",
                    "watch|wear": "Smartwatch",
                    "camera|cam|webcam": "Camera",
                    "echo|alexa|dot": "SmartSpeaker",
                    "hue|lifx|bulb": "SmartLight",
                    "server|nas": "Server",
                    "playstation|xbox|switch": "GamingConsole",
                    "raspberry|pi": "IoT",
                    "google|chromecast|nest": "SmartHome",
                    "doorbell|lock|security": "SecurityDevice",
                }
                for pattern, type_key in type_name_patterns.items():
                    if re.search(pattern, name, re.IGNORECASE):
                        type_ = DEVICE_TYPES.get(type_key, default_type)
                        break
                else:
                    # IP-based type guessing
                    type_ip_patterns = {
                        r"^192\.168\.[0-1]\.1$": "Router",
                        r"^10\.0\.0\.1$": "Router",
                        r"^192\.168\.[0-1]\.[2-9]$": "Desktop",
                        r"^192\.168\.[0-1]\.1\d{2}$": "Phone",
                    }
                    for pattern, type_key in type_ip_patterns.items():
                        if re.match(pattern, ip):
                            type_ = DEVICE_TYPES.get(type_key, default_type)
                            break
                    else:
                        type_ = default_type

    return icon, type_

# Deprecated functions with redirects (To be removed once all calls for these have been adjusted to use the updated function)
def guess_icon(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default: str
    ) -> str:
    """
    [DEPRECATED] Guess the appropriate FontAwesome icon for a device based on its attributes.
    Use guess_device_attributes instead.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default: Default icon to return if no match is found.

    Returns:
        str: Base64-encoded FontAwesome icon HTML string.
    """
    warnings.warn("guess_icon is deprecated; use guess_device_attributes instead", DeprecationWarning)
    icon, _ = guess_device_attributes(vendor, mac, ip, name, default, "unknown_type")
    return icon

def guess_type(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default: str
    ) -> str:
    """
    [DEPRECATED] Guess the device type based on its attributes.
    Use guess_device_attributes instead.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default: Default type to return if no match is found.

    Returns:
        str: Device type from DEVICE_TYPES dictionary.
    """
    warnings.warn("guess_type is deprecated; use guess_device_attributes instead", DeprecationWarning)
    _, type_ = guess_device_attributes(vendor, mac, ip, name, "unknown_icon", default)
    return type_
    
    # Handler for when this is run as a program instead of called as a module.
    if __name__ == "__main__":
    mylog('error', "This module is not intended to be run directly.")