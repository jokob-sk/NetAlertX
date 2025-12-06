from logger import mylog


# -------------------------------------------------------------------------------
# Device object handling (WIP)
# -------------------------------------------------------------------------------
class DeviceInstance:
    def __init__(self, db):
        self.db = db

    # Get all
    def getAll(self):
        self.db.sql.execute("""
            SELECT * FROM Devices
        """)
        return self.db.sql.fetchall()

    # Get all with unknown names
    def getUnknown(self):
        self.db.sql.execute("""
            SELECT * FROM Devices WHERE devName in ("(unknown)", "(name not found)", "" )
        """)
        return self.db.sql.fetchall()

    # Get specific column value based on devMac
    def getValueWithMac(self, column_name, devMac):
        query = f"SELECT {column_name} FROM Devices WHERE devMac = ?"
        self.db.sql.execute(query, (devMac,))
        result = self.db.sql.fetchone()
        return result[column_name] if result else None

    # Get all down
    def getDown(self):
        self.db.sql.execute("""
            SELECT * FROM Devices WHERE devAlertDown = 1 and devPresentLastScan = 0
        """)
        return self.db.sql.fetchall()

    # Get all down
    def getOffline(self):
        self.db.sql.execute("""
            SELECT * FROM Devices WHERE devPresentLastScan = 0
        """)
        return self.db.sql.fetchall()

    # Get a device by devGUID
    def getByGUID(self, devGUID):
        self.db.sql.execute("SELECT * FROM Devices WHERE devGUID = ?", (devGUID,))
        result = self.db.sql.fetchone()
        return dict(result) if result else None

    # Check if a device exists by devGUID
    def exists(self, devGUID):
        self.db.sql.execute(
            "SELECT COUNT(*) AS count FROM Devices WHERE devGUID = ?", (devGUID,)
        )
        result = self.db.sql.fetchone()
        return result["count"] > 0

    # Get a device by its last IP address
    def getByIP(self, ip):
        self.db.sql.execute("SELECT * FROM Devices WHERE devLastIP = ?", (ip,))
        row = self.db.sql.fetchone()
        return dict(row) if row else None

    # Search devices by partial mac, name or IP
    def search(self, query):
        like = f"%{query}%"
        self.db.sql.execute(
            "SELECT * FROM Devices WHERE devMac LIKE ? OR devName LIKE ? OR devLastIP LIKE ?",
            (like, like, like),
        )
        rows = self.db.sql.fetchall()
        return [dict(r) for r in rows]

    # Get the most recently discovered device
    def getLatest(self):
        self.db.sql.execute("SELECT * FROM Devices ORDER BY devFirstConnection DESC LIMIT 1")
        row = self.db.sql.fetchone()
        return dict(row) if row else None

    def getNetworkTopology(self):
        """Returns nodes and links for the current Devices table.

        Nodes: {id, name, vendor}
        Links: {source, target, port}
        """
        self.db.sql.execute("SELECT devName, devMac, devParentMAC, devParentPort, devVendor FROM Devices")
        rows = self.db.sql.fetchall()
        nodes = []
        links = []
        for row in rows:
            nodes.append({"id": row['devMac'], "name": row['devName'], "vendor": row['devVendor']})
            if row['devParentMAC']:
                links.append({"source": row['devParentMAC'], "target": row['devMac'], "port": row['devParentPort']})
        return {"nodes": nodes, "links": links}

    # Update a specific field for a device
    def updateField(self, devGUID, field, value):
        if not self.exists(devGUID):
            m = f"[Device] In 'updateField': GUID {devGUID} not found."
            mylog("none", m)
            raise ValueError(m)

        self.db.sql.execute(
            f"""
            UPDATE Devices SET {field} = ? WHERE devGUID = ?
        """,
            (value, devGUID),
        )
        self.db.commitDB()

    # Delete a device by devGUID
    def delete(self, devGUID):
        if not self.exists(devGUID):
            m = f"[Device] In 'delete': GUID {devGUID} not found."
            mylog("none", m)
            raise ValueError(m)

        self.db.sql.execute("DELETE FROM Devices WHERE devGUID = ?", (devGUID,))
        self.db.commitDB()
