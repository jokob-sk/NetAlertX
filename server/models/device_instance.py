from front.plugins.plugin_helper import is_mac
from logger import mylog
from models.plugin_object_instance import PluginObjectInstance
from database import get_temp_db_connection


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
