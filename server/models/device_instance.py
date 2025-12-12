import os
import base64
import re
import sqlite3
import csv
from io import StringIO
from front.plugins.plugin_helper import is_mac
from logger import mylog
from models.plugin_object_instance import PluginObjectInstance
from database import get_temp_db_connection
from db.db_helper import get_table_json, get_device_condition_by_status, row_to_json, get_date_from_period
from helper import is_random_mac, get_setting_value
from utils.datetime_utils import timeNowDB, format_date


class DeviceInstance:

    # --- helpers --------------------------------------------------------------
    def _fetchall(self, query, params=()):
        conn = get_temp_db_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _fetchone(self, query, params=()):
        conn = get_temp_db_connection()
        row = conn.execute(query, params).fetchone()
        conn.close()
        return dict(row) if row else None

    def _execute(self, query, params=()):
        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        conn.close()

    # --- public API -----------------------------------------------------------
    def getAll(self):
        return self._fetchall("SELECT * FROM Devices")

    def getUnknown(self):
        return self._fetchall("""
            SELECT * FROM Devices
            WHERE devName IN ("(unknown)", "(name not found)", "")
        """)

    def getValueWithMac(self, column_name, devMac):
        row = self._fetchone(f"""
            SELECT {column_name} FROM Devices WHERE devMac = ?
        """, (devMac,))
        return row.get(column_name) if row else None

    def getDown(self):
        return self._fetchall("""
            SELECT * FROM Devices
            WHERE devAlertDown = 1 AND devPresentLastScan = 0
        """)

    def getOffline(self):
        return self._fetchall("""
            SELECT * FROM Devices
            WHERE devPresentLastScan = 0
        """)

    def getByGUID(self, devGUID):
        return self._fetchone("""
            SELECT * FROM Devices WHERE devGUID = ?
        """, (devGUID,))

    def exists(self, devGUID):
        row = self._fetchone("""
            SELECT COUNT(*) as count FROM Devices WHERE devGUID = ?
        """, (devGUID,))
        return row['count'] > 0 if row else False

    def getByIP(self, ip):
        return self._fetchone("""
            SELECT * FROM Devices WHERE devLastIP = ?
        """, (ip,))

    def search(self, query):
        like = f"%{query}%"
        return self._fetchall("""
            SELECT * FROM Devices
            WHERE devMac LIKE ? OR devName LIKE ? OR devLastIP LIKE ?
        """, (like, like, like))

    def getLatest(self):
        return self._fetchone("""
            SELECT * FROM Devices
            ORDER BY devFirstConnection DESC LIMIT 1
        """)

    def getFavorite(self):
        return self._fetchall("""
            SELECT * FROM Devices
            WHERE devFavorite = 1
        """)

    def getNetworkTopology(self):
        rows = self._fetchall("""
            SELECT devName, devMac, devParentMAC, devParentPort, devVendor FROM Devices
        """)
        nodes = [{"id": r["devMac"], "name": r["devName"], "vendor": r["devVendor"]} for r in rows]
        links = [{"source": r["devParentMAC"], "target": r["devMac"], "port": r["devParentPort"]}
                 for r in rows if r["devParentMAC"]]
        return {"nodes": nodes, "links": links}

    def updateField(self, devGUID, field, value):
        if not self.exists(devGUID):
            msg = f"[Device] updateField: GUID {devGUID} not found"
            mylog("none", msg)
            raise ValueError(msg)
        self._execute(f"UPDATE Devices SET {field}=? WHERE devGUID=?", (value, devGUID))

    def delete(self, devGUID):
        if not self.exists(devGUID):
            msg = f"[Device] delete: GUID {devGUID} not found"
            mylog("none", msg)
            raise ValueError(msg)
        self._execute("DELETE FROM Devices WHERE devGUID=?", (devGUID,))

    def resolvePrimaryID(self, target):
        if is_mac(target):
            return target.lower()
        dev = self.getByIP(target)
        return dev['devMac'].lower() if dev else None

    def getOpenPorts(self, target):
        primary = self.resolvePrimaryID(target)
        if not primary:
            return []

        objs = PluginObjectInstance().getByField(
            plugPrefix='NMAP',
            matchedColumn='Object_PrimaryID',
            matchedKey=primary,
            returnFields=['Object_SecondaryID', 'Watched_Value2']
        )

        ports = []
        for o in objs:

            port = int(o.get('Object_SecondaryID') or 0)

            ports.append({"port": port, "service": o.get('Watched_Value2', '')})

        return ports

    # --- devices_endpoint.py methods (HTTP response layer) -------------------

    def getAll_AsResponse(self):
        """Return all devices as raw data (not jsonified)."""
        return self.getAll()

    def deleteDevices(self, macs):
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
            return {"success": True, "deleted": "all"}

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

        return {"success": True, "deleted_count": deleted_count}

    def deleteAllWithEmptyMacs(self):
        """Delete devices with empty MAC addresses."""
        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Devices WHERE devMAC IS NULL OR devMAC = ''")
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        return {"success": True, "deleted": deleted}

    def deleteUnknownDevices(self):
        """Delete devices marked as unknown."""
        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(
            """DELETE FROM Devices WHERE devName='(unknown)' OR devName='(name not found)'"""
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        return {"success": True, "deleted": deleted}

    def exportDevices(self, export_format):
        """
        Export devices from the Devices table in the desired format.
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
            return {
                "format": "json",
                "data": [row for row in devices_json["data"]],
                "columns": list(columns)
            }
        elif export_format == "csv":
            si = StringIO()
            writer = csv.DictWriter(si, fieldnames=columns, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in devices_json.json["data"]:
                writer.writerow(row)
            return {
                "format": "csv",
                "content": si.getvalue(),
            }
        else:
            return {"error": f"Unsupported format '{export_format}'"}

    def importCSV(self, file_storage=None, json_content=None):
        """
        Import devices from CSV.
        - json_content: base64-encoded CSV string
        - file_storage: uploaded file object
        - fallback: read from config/devices.csv
        """
        data = ""
        skipped = []

        # 1. Try JSON `content` (base64-encoded CSV)
        if json_content:
            try:
                data = base64.b64decode(json_content, validate=True).decode("utf-8")
            except Exception as e:
                return {"success": False, "error": f"Base64 decode failed: {e}"}

        # 2. Otherwise, try uploaded file
        elif file_storage:
            try:
                data = file_storage.read().decode("utf-8")
            except Exception as e:
                return {"success": False, "error": f"File read failed: {e}"}

        # 3. Fallback: try local file (same as PHP `$file = '../../../config/devices.csv';`)
        else:
            config_root = os.environ.get("NETALERTX_CONFIG", "/data/config")
            local_file = os.path.join(config_root, "devices.csv")
            try:
                with open(local_file, "r", encoding="utf-8") as f:
                    data = f.read()
            except FileNotFoundError:
                return {"success": False, "error": "CSV file missing"}

        if not data:
            return {"success": False, "error": "No CSV data found"}

        # --- Clean up newlines inside quoted fields ---
        data = re.sub(r'"([^"]*)"', lambda m: m.group(0).replace("\n", " "), data)

        # --- Parse CSV ---
        lines = data.splitlines()
        reader = csv.reader(lines)
        try:
            header = [h.strip() for h in next(reader)]
        except StopIteration:
            return {"success": False, "error": "CSV missing header"}

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

        return {"success": True, "inserted": row_count, "skipped_lines": skipped}

    def getTotals(self):
        """Get device totals by status."""
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
        row = sql.fetchone()
        conn.close()

        return list(row) if row else []

    def getByStatus(self, status=None):
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

            # Start with all fields from the device record
            device_record = r.copy()
            # Override with formatted fields
            device_record["id"] = r.get("devMac", "")
            device_record["title"] = dev_name
            device_record["favorite"] = r.get("devFavorite", 0)

            table_data.append(device_record)

        conn.close()
        return table_data

    # --- device_endpoint.py methods -------------------------------------------

    def getDeviceData(self, mac, period=""):
        """Fetch device info with children, event stats, and presence calculation."""
        now = timeNowDB()

        # Special case for new device
        if mac.lower() == "new":
            device_data = {
                "devMac": "",
                "devName": "",
                "devOwner": "",
                "devType": "",
                "devVendor": "",
                "devFavorite": 0,
                "devGroup": "",
                "devComments": "",
                "devFirstConnection": now,
                "devLastConnection": now,
                "devLastIP": "",
                "devStaticIP": 0,
                "devScan": 0,
                "devLogEvents": 0,
                "devAlertEvents": 0,
                "devAlertDown": 0,
                "devParentRelType": "default",
                "devReqNicsOnline": 0,
                "devSkipRepeated": 0,
                "devLastNotification": "",
                "devPresentLastScan": 0,
                "devIsNew": 1,
                "devLocation": "",
                "devIsArchived": 0,
                "devParentMAC": "",
                "devParentPort": "",
                "devIcon": "",
                "devGUID": "",
                "devSite": "",
                "devSSID": "",
                "devSyncHubNode": "",
                "devSourcePlugin": "",
                "devCustomProps": "",
                "devStatus": "Unknown",
                "devIsRandomMAC": False,
                "devSessions": 0,
                "devEvents": 0,
                "devDownAlerts": 0,
                "devPresenceHours": 0,
                "devFQDN": "",
            }
            return device_data

        # Compute period date for sessions/events
        period_date_sql = get_date_from_period(period)

        # Fetch device info + computed fields
        sql = f"""
        SELECT
            d.*,
            CASE
                WHEN d.devAlertDown != 0 AND d.devPresentLastScan = 0 THEN 'Down'
                WHEN d.devPresentLastScan = 1 THEN 'On-line'
                ELSE 'Off-line'
            END AS devStatus,

            (SELECT COUNT(*) FROM Sessions
             WHERE ses_MAC = d.devMac AND (
                ses_DateTimeConnection >= {period_date_sql} OR
                ses_DateTimeDisconnection >= {period_date_sql} OR
                ses_StillConnected = 1
             )) AS devSessions,

            (SELECT COUNT(*) FROM Events
             WHERE eve_MAC = d.devMac AND eve_DateTime >= {period_date_sql}
               AND eve_EventType NOT IN ('Connected','Disconnected')) AS devEvents,

            (SELECT COUNT(*) FROM Events
             WHERE eve_MAC = d.devMac AND eve_DateTime >= {period_date_sql}
               AND eve_EventType = 'Device Down') AS devDownAlerts,

            (SELECT CAST(MAX(0, SUM(
                julianday(IFNULL(ses_DateTimeDisconnection,'{now}')) -
                julianday(CASE WHEN ses_DateTimeConnection < {period_date_sql}
                               THEN {period_date_sql} ELSE ses_DateTimeConnection END)
            ) * 24) AS INT)
             FROM Sessions
             WHERE ses_MAC = d.devMac
               AND ses_DateTimeConnection IS NOT NULL
               AND (ses_DateTimeDisconnection IS NOT NULL OR ses_StillConnected = 1)
               AND (ses_DateTimeConnection >= {period_date_sql}
                    OR ses_DateTimeDisconnection >= {period_date_sql} OR ses_StillConnected = 1)
            ) AS devPresenceHours

        FROM Devices d
        WHERE d.devMac = ? OR CAST(d.rowid AS TEXT) = ?
        """

        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(sql, (mac, mac))
        row = cur.fetchone()

        if not row:
            conn.close()
            return None

        device_data = row_to_json(list(row.keys()), row)
        device_data["devFirstConnection"] = format_date(device_data["devFirstConnection"])
        device_data["devLastConnection"] = format_date(device_data["devLastConnection"])
        device_data["devIsRandomMAC"] = is_random_mac(device_data["devMac"])

        # Fetch children
        cur.execute(
            "SELECT * FROM Devices WHERE devParentMAC = ? ORDER BY devPresentLastScan DESC",
            (device_data["devMac"],),
        )
        children_rows = cur.fetchall()
        children = [row_to_json(list(r.keys()), r) for r in children_rows]
        children_nics = [c for c in children if c.get("devParentRelType") == "nic"]

        device_data["devChildrenDynamic"] = children
        device_data["devChildrenNicsDynamic"] = children_nics

        conn.close()
        return device_data

    def setDeviceData(self, mac, data):
        """Update or create a device."""
        if data.get("createNew", False):
            sql = """
            INSERT INTO Devices (
                devMac, devName, devOwner, devType, devVendor, devIcon,
                devFavorite, devGroup, devLocation, devComments,
                devParentMAC, devParentPort, devSSID, devSite,
                devStaticIP, devScan, devAlertEvents, devAlertDown,
                devParentRelType, devReqNicsOnline, devSkipRepeated,
                devIsNew, devIsArchived, devLastConnection,
                devFirstConnection, devLastIP, devGUID, devCustomProps,
                devSourcePlugin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                mac,
                data.get("devName", ""),
                data.get("devOwner", ""),
                data.get("devType", ""),
                data.get("devVendor", ""),
                data.get("devIcon", ""),
                data.get("devFavorite", 0),
                data.get("devGroup", ""),
                data.get("devLocation", ""),
                data.get("devComments", ""),
                data.get("devParentMAC", ""),
                data.get("devParentPort", ""),
                data.get("devSSID", ""),
                data.get("devSite", ""),
                data.get("devStaticIP", 0),
                data.get("devScan", 0),
                data.get("devAlertEvents", 0),
                data.get("devAlertDown", 0),
                data.get("devParentRelType", "default"),
                data.get("devReqNicsOnline", 0),
                data.get("devSkipRepeated", 0),
                data.get("devIsNew", 0),
                data.get("devIsArchived", 0),
                data.get("devLastConnection", timeNowDB()),
                data.get("devFirstConnection", timeNowDB()),
                data.get("devLastIP", ""),
                data.get("devGUID", ""),
                data.get("devCustomProps", ""),
                data.get("devSourcePlugin", "DUMMY"),
            )

        else:
            sql = """
            UPDATE Devices SET
                devName=?, devOwner=?, devType=?, devVendor=?, devIcon=?,
                devFavorite=?, devGroup=?, devLocation=?, devComments=?,
                devParentMAC=?, devParentPort=?, devSSID=?, devSite=?,
                devStaticIP=?, devScan=?, devAlertEvents=?, devAlertDown=?,
                devParentRelType=?, devReqNicsOnline=?, devSkipRepeated=?,
                devIsNew=?, devIsArchived=?, devCustomProps=?
            WHERE devMac=?
            """
            values = (
                data.get("devName", ""),
                data.get("devOwner", ""),
                data.get("devType", ""),
                data.get("devVendor", ""),
                data.get("devIcon", ""),
                data.get("devFavorite", 0),
                data.get("devGroup", ""),
                data.get("devLocation", ""),
                data.get("devComments", ""),
                data.get("devParentMAC", ""),
                data.get("devParentPort", ""),
                data.get("devSSID", ""),
                data.get("devSite", ""),
                data.get("devStaticIP", 0),
                data.get("devScan", 0),
                data.get("devAlertEvents", 0),
                data.get("devAlertDown", 0),
                data.get("devParentRelType", "default"),
                data.get("devReqNicsOnline", 0),
                data.get("devSkipRepeated", 0),
                data.get("devIsNew", 0),
                data.get("devIsArchived", 0),
                data.get("devCustomProps", ""),
                mac,
            )

        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        conn.close()
        return {"success": True}

    def deleteDeviceByMAC(self, mac):
        """Delete a device by MAC."""
        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Devices WHERE devMac=?", (mac,))
        conn.commit()
        conn.close()
        return {"success": True}

    def deleteDeviceEvents(self, mac):
        """Delete all events for a device."""
        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Events WHERE eve_MAC=?", (mac,))
        conn.commit()
        conn.close()
        return {"success": True}

    def resetDeviceProps(self, mac):
        """Reset device custom properties to default."""
        default_props = get_setting_value("NEWDEV_devCustomProps")
        conn = get_temp_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE Devices SET devCustomProps=? WHERE devMac=?",
            (default_props, mac),
        )
        conn.commit()
        conn.close()
        return {"success": True}

    def updateDeviceColumn(self, mac, column_name, column_value):
        """Update a specific column for a given device."""
        conn = get_temp_db_connection()
        cur = conn.cursor()

        # Build safe SQL with column name
        sql = f"UPDATE Devices SET {column_name}=? WHERE devMac=?"
        cur.execute(sql, (column_value, mac))
        conn.commit()

        if cur.rowcount > 0:
            result = {"success": True}
        else:
            result = {"success": False, "error": "Device not found"}

        conn.close()
        return result

    def copyDevice(self, mac_from, mac_to):
        """Copy a device entry from one MAC to another."""
        conn = get_temp_db_connection()
        cur = conn.cursor()

        try:
            # Drop temporary table if exists
            cur.execute("DROP TABLE IF EXISTS temp_devices")

            # Create temporary table with source device
            cur.execute(
                "CREATE TABLE temp_devices AS SELECT * FROM Devices WHERE devMac = ?",
                (mac_from,),
            )

            # Update temporary table to target MAC
            cur.execute("UPDATE temp_devices SET devMac = ?", (mac_to,))

            # Delete previous entry with target MAC
            cur.execute("DELETE FROM Devices WHERE devMac = ?", (mac_to,))

            # Insert new entry from temporary table
            cur.execute(
                "INSERT INTO Devices SELECT * FROM temp_devices WHERE devMac = ?", (mac_to,)
            )

            # Drop temporary table
            cur.execute("DROP TABLE temp_devices")

            conn.commit()
            return {
                "success": True,
                "message": f"Device copied from {mac_from} to {mac_to}",
            }

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}

        finally:
            conn.close()
