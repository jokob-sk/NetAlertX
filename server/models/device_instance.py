import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog

#-------------------------------------------------------------------------------
# Device object handling (WIP)
#-------------------------------------------------------------------------------
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
        self.db.sql.execute("SELECT COUNT(*) AS count FROM Devices WHERE devGUID = ?", (devGUID,))
        result = self.db.sql.fetchone()
        return result["count"] > 0

    # Update a specific field for a device
    def updateField(self, devGUID, field, value):
        if not self.exists(devGUID):
            m = f"[Device] In 'updateField': GUID {devGUID} not found."
            mylog('none', m)
            raise ValueError(m)

        self.db.sql.execute(f"""
            UPDATE Devices SET {field} = ? WHERE devGUID = ?
        """, (value, devGUID))
        self.db.commitDB()

    # Delete a device by devGUID
    def delete(self, devGUID):
        if not self.exists(devGUID):
            m = f"[Device] In 'delete': GUID {devGUID} not found."
            mylog('none', m)
            raise ValueError(m)

        self.db.sql.execute("DELETE FROM Devices WHERE devGUID = ?", (devGUID,))
        self.db.commitDB()