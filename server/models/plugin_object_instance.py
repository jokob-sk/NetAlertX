import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog

#-------------------------------------------------------------------------------
# Plugin object handling (WIP)
#-------------------------------------------------------------------------------
class PluginObjectInstance:
    def __init__(self, db):
        self.db = db

    # Get all plugin objects
    def getAll(self):
        self.db.sql.execute("""
            SELECT * FROM Plugins_Objects
        """)
        return self.db.sql.fetchall()
    
    # Get plugin object by ObjectGUID
    def getByGUID(self, ObjectGUID):
        self.db.sql.execute("SELECT * FROM Plugins_Objects WHERE ObjectGUID = ?", (ObjectGUID,))
        result = self.db.sql.fetchone()
        return dict(result) if result else None

    # Check if a plugin object exists by ObjectGUID
    def exists(self, ObjectGUID):
        self.db.sql.execute("SELECT COUNT(*) AS count FROM Plugins_Objects WHERE ObjectGUID = ?", (ObjectGUID,))
        result = self.db.sql.fetchone()
        return result["count"] > 0

    # Get objects by plugin name
    def getByPlugin(self, plugin):
        self.db.sql.execute("SELECT * FROM Plugins_Objects WHERE Plugin = ?", (plugin,))
        return self.db.sql.fetchall()
    
    # Get objects by status
    def getByStatus(self, status):
        self.db.sql.execute("SELECT * FROM Plugins_Objects WHERE Status = ?", (status,))
        return self.db.sql.fetchall()
    
    # Update a specific field for a plugin object
    def updateField(self, ObjectGUID, field, value):
        if not self.exists(ObjectGUID):
            m = f"[PluginObject] In 'updateField': GUID {ObjectGUID} not found."
            mylog('none', m)
            raise ValueError(m)

        self.db.sql.execute(f"""
            UPDATE Plugins_Objects SET {field} = ? WHERE ObjectGUID = ?
        """, (value, ObjectGUID))
        self.db.commitDB()
    
    # Delete a plugin object by ObjectGUID
    def delete(self, ObjectGUID):
        if not self.exists(ObjectGUID):
            m = f"[PluginObject] In 'delete': GUID {ObjectGUID} not found."
            mylog('none', m)
            raise ValueError(m)

        self.db.sql.execute("DELETE FROM Plugins_Objects WHERE ObjectGUID = ?", (ObjectGUID,))
        self.db.commitDB()
