import datetime
import json
import uuid
import sys
import pytz

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

# Register NetAlertX modules 
import conf
from helper import get_setting_value, timeNowTZ
# Make sure the TIMEZONE for logging is correct
# conf.tz = pytz.timezone(get_setting_value('TIMEZONE'))

from logger import mylog, Logger, print_log, logResult

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

from const import applicationPath, logPath, apiPath, confFileName, sql_generateGuid
from helper import  timeNowTZ


#-------------------------------------------------------------------------------
# Execution object handling
#-------------------------------------------------------------------------------
class AppEvent_obj:
    def __init__(self, db):
        self.db = db

        # drop table 
        self.db.sql.execute("""DROP TABLE IF EXISTS "AppEvents" """)

        # Drop all triggers
        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_create_device;')
        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_read_device;')
        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_update_device;')
        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_delete_device;')

        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_delete_plugin_object;')
        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_create_plugin_object;')
        self.db.sql.execute('DROP TRIGGER IF EXISTS trg_update_plugin_object;')

        # Create AppEvent table if missing
        self.db.sql.execute("""CREATE TABLE IF NOT EXISTS "AppEvents" (
            "Index"                 INTEGER,
            "GUID"                  TEXT UNIQUE,
            "AppEventProcessed"     BOOLEAN,
            "DateTimeCreated"       TEXT,
            "ObjectType"            TEXT, -- ObjectType (Plugins, Notifications, Events)
            "ObjectGUID"            TEXT,
            "ObjectPlugin"          TEXT,
            "ObjectPrimaryID"       TEXT,
            "ObjectSecondaryID"     TEXT,
            "ObjectForeignKey"      TEXT,
            "ObjectIndex"           TEXT,            
            "ObjectIsNew"           BOOLEAN, 
            "ObjectIsArchived"      BOOLEAN, 
            "ObjectStatusColumn"    TEXT, -- Status (Notifications, Plugins), eve_EventType (Events)
            "ObjectStatus"          TEXT, -- new_devices, down_devices, events, new, watched-changed, watched-not-changed, missing-in-last-scan, Device down, New Device, IP Changed, Connected, Disconnected, VOIDED - Disconnected, VOIDED - Connected, <missing event>            
            "AppEventType"          TEXT, -- "create", "update", "delete" (+TBD)
            "Helper1"               TEXT,
            "Helper2"               TEXT,
            "Helper3"               TEXT,
            "Extra"                 TEXT,            
            PRIMARY KEY("Index" AUTOINCREMENT)
        );
        """)

        # -------------
        # Device events

        sql_devices_mappedColumns = '''
                    "GUID",
                    "DateTimeCreated",
                    "AppEventProcessed",
                    "ObjectType",
                    "ObjectGUID",
                    "ObjectPrimaryID",
                    "ObjectSecondaryID",
                    "ObjectStatus",
                    "ObjectStatusColumn",
                    "ObjectIsNew",
                    "ObjectIsArchived",
                    "ObjectForeignKey",
                    "AppEventType"
        '''

        # Trigger for create event
        self.db.sql.execute(f'''
            CREATE TRIGGER IF NOT EXISTS "trg_create_device"
            AFTER INSERT ON "Devices"
            BEGIN
                INSERT INTO "AppEvents" (
                    {sql_devices_mappedColumns}
                )
                VALUES (                    
                    {sql_generateGuid},
                    DATETIME('now'),
                    FALSE,
                    'Devices',
                    NEW.devGUID,
                    NEW.devMac,
                    NEW.devLastIP,
                    CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END,
                    'devPresentLastScan',
                    NEW.devIsNew,
                    NEW.devIsArchived,
                    NEW.devMac,
                    'create'
                );
            END;
        ''')

        # 🔴 This would generate too many events, disabled for now
        # # Trigger for read event
        # self.db.sql.execute('''
        #     TODO
        # ''')

        # Trigger for update event
        self.db.sql.execute(f'''
            CREATE TRIGGER IF NOT EXISTS "trg_update_device"
            AFTER UPDATE ON "Devices"
            BEGIN
                INSERT INTO "AppEvents" (
                    {sql_devices_mappedColumns}
                )
                VALUES (                    
                    {sql_generateGuid},
                    DATETIME('now'),
                    FALSE,
                    'Devices',
                    NEW.devGUID,
                    NEW.devMac,
                    NEW.devLastIP,
                    CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END,
                    'devPresentLastScan',
                    NEW.devIsNew,
                    NEW.devIsArchived,
                    NEW.devMac,
                    'update'
                );
            END;
        ''')

        # Trigger for delete event
        self.db.sql.execute(f'''
            CREATE TRIGGER IF NOT EXISTS "trg_delete_device"
            AFTER DELETE ON "Devices"
            BEGIN
                INSERT INTO "AppEvents" (
                    {sql_devices_mappedColumns}
                )
                VALUES (                    
                    {sql_generateGuid},
                    DATETIME('now'),
                    FALSE,
                    'Devices',
                    OLD.devGUID,
                    OLD.devMac,
                    OLD.devLastIP,
                    CASE WHEN OLD.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END,
                    'devPresentLastScan',
                    OLD.devIsNew,
                    OLD.devIsArchived,
                    OLD.devMac,
                    'delete'
                );
            END;
        ''')


        # -------------
        # Plugins_Objects events

        sql_plugins_objects_mappedColumns = '''
                    "GUID",
                    "DateTimeCreated",
                    "AppEventProcessed",
                    "ObjectType",                    
                    "ObjectGUID",                    
                    "ObjectPlugin",
                    "ObjectPrimaryID",
                    "ObjectSecondaryID",
                    "ObjectForeignKey",
                    "ObjectStatusColumn",
                    "ObjectStatus",
                    "AppEventType"
        '''

        # Create trigger for update event on Plugins_Objects
        self.db.sql.execute(f'''
            CREATE TRIGGER IF NOT EXISTS trg_update_plugin_object
            AFTER UPDATE ON Plugins_Objects
            BEGIN
                INSERT INTO AppEvents (
                   {sql_plugins_objects_mappedColumns}
                )
                VALUES (
                    {sql_generateGuid},
                    DATETIME('now'),
                    FALSE,
                    'Plugins_Objects',   
                    NEW.ObjectGUID,                 
                    NEW.Plugin,                    
                    NEW.Object_PrimaryID,
                    NEW.Object_SecondaryID,
                    NEW.ForeignKey,
                    'Status',
                    NEW.Status,
                    'update'
                );
            END;
        ''')

        # Create trigger for CREATE event on Plugins_Objects
        self.db.sql.execute(f'''
            CREATE TRIGGER IF NOT EXISTS trg_create_plugin_object
            AFTER INSERT ON Plugins_Objects
            BEGIN
                INSERT INTO AppEvents (
                {sql_plugins_objects_mappedColumns}
                )
                VALUES (
                    {sql_generateGuid},
                    DATETIME('now'),
                    FALSE,
                    'Plugins_Objects',
                    NEW.ObjectGUID, 
                    NEW.Plugin,
                    NEW.Object_PrimaryID,
                    NEW.Object_SecondaryID,
                    NEW.ForeignKey,
                    'Status',
                    NEW.Status,
                    'create'
                );
            END;
        ''')

        # Create trigger for DELETE event on Plugins_Objects
        self.db.sql.execute(f'''
            CREATE TRIGGER IF NOT EXISTS trg_delete_plugin_object
            AFTER DELETE ON Plugins_Objects
            BEGIN
                INSERT INTO AppEvents (
                {sql_plugins_objects_mappedColumns}
                )
                VALUES (
                    {sql_generateGuid},
                    DATETIME('now'),
                    FALSE,
                    'Plugins_Objects',
                    OLD.ObjectGUID, 
                    OLD.Plugin,
                    OLD.Object_PrimaryID,
                    OLD.Object_SecondaryID,
                    OLD.ForeignKey,
                    'Status',
                    OLD.Status,
                    'delete'
                );
            END;
        ''')

        self.save()

    # -------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------
    # below code is unused
    # -------------------------------------------------------------------------------

    # Create a new DB entry if new notifications are available, otherwise skip
    def create(self, Extra="", **kwargs):
        # Check if nothing to report, end
        if not any(kwargs.values()):
            return False

        # Continue and save into DB if notifications are available
        self.GUID = str(uuid.uuid4())
        self.DateTimeCreated = timeNowTZ()
        self.ObjectType = "Plugins"  # Modify ObjectType as needed

        # Optional parameters
        self.ObjectGUID         = kwargs.get("ObjectGUID", "")
        self.ObjectPlugin       = kwargs.get("ObjectPlugin", "")
        self.ObjectMAC          = kwargs.get("ObjectMAC", "")
        self.ObjectIP           = kwargs.get("ObjectIP", "")
        self.ObjectPrimaryID    = kwargs.get("ObjectPrimaryID", "")
        self.ObjectSecondaryID  = kwargs.get("ObjectSecondaryID", "")
        self.ObjectForeignKey   = kwargs.get("ObjectForeignKey", "")
        self.ObjectIndex        = kwargs.get("ObjectIndex", "")
        self.ObjectRowID        = kwargs.get("ObjectRowID", "")
        self.ObjectStatusColumn = kwargs.get("ObjectStatusColumn", "")
        self.ObjectStatus       = kwargs.get("ObjectStatus", "")

        self.AppEventStatus = "new"  # Modify AppEventStatus as needed
        self.Extra = Extra

        self.upsert()

        return True

    def upsert(self):
        self.db.sql.execute("""
            INSERT OR REPLACE INTO AppEvents (
                "GUID", 
                "DateTimeCreated", 
                "ObjectType", 
                "ObjectGUID", 
                "ObjectPlugin", 
                "ObjectMAC", 
                "ObjectIP", 
                "ObjectPrimaryID", 
                "ObjectSecondaryID", 
                "ObjectForeignKey", 
                "ObjectIndex", 
                "ObjectRowID", 
                "ObjectStatusColumn", 
                "ObjectStatus", 
                "AppEventStatus", 
                "Extra"
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.GUID, 
            self.DateTimeCreated, 
            self.ObjectType, 
            self.ObjectGUID, 
            self.ObjectPlugin, 
            self.ObjectMAC, 
            self.ObjectIP, 
            self.ObjectPrimaryID, 
            self.ObjectSecondaryID, 
            self.ObjectForeignKey, 
            self.ObjectIndex, 
            self.ObjectRowID, 
            self.ObjectStatusColumn, 
            self.ObjectStatus, 
            self.AppEventStatus, 
            self.Extra
        ))

        self.save()

    def save(self):
        # Commit changes
        self.db.commitDB()


def getPluginObject(**kwargs):

    # Check if nothing, end
    if not any(kwargs.values()):
            return None

    # Optional parameters
    GUID          = kwargs.get("GUID", "")
    Plugin        = kwargs.get("Plugin", "")
    MAC           = kwargs.get("MAC", "")
    IP            = kwargs.get("IP", "")
    PrimaryID     = kwargs.get("PrimaryID", "")
    SecondaryID   = kwargs.get("SecondaryID", "")
    ForeignKey    = kwargs.get("ForeignKey", "")
    Index         = kwargs.get("Index", "")
    RowID         = kwargs.get("RowID", "")

    # we need the plugin
    if Plugin == "":
        return None

    plugins_objects = apiPath + 'table_plugins_objects.json'

    try:
        with open(plugins_objects, 'r') as json_file:

            data = json.load(json_file)

            for item in data.get("data",[]):
                if item.get("Index") == Index:
                    return item

            for item in data.get("data",[]):
                if item.get("ObjectPrimaryID") == PrimaryID and item.get("ObjectSecondaryID") == SecondaryID:                    
                    return item
            
            for item in data.get("data",[]):
                if item.get("ObjectPrimaryID") == MAC and item.get("ObjectSecondaryID") == IP:
                    return item

            for item in data.get("data",[]):
                if item.get("ObjectPrimaryID") == PrimaryID and item.get("ObjectSecondaryID") == IP:
                    return item

            for item in data.get("data",[]):
                if item.get("ObjectPrimaryID") == MAC and item.get("ObjectSecondaryID") == IP:
                    return item
                

            mylog('debug', [f'[{module_name}] ⚠ ERROR - Object not found - GUID:{GUID} | Plugin:{Plugin} | MAC:{MAC} | IP:{IP} | PrimaryID:{PrimaryID} | SecondaryID:{SecondaryID} | ForeignKey:{ForeignKey} | Index:{Index} | RowID:{RowID} '])  

            return None

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        # Handle the case when the file is not found, JSON decoding fails, or data is not in the expected format
        mylog('none', [f'[{module_name}] ⚠ ERROR - JSONDecodeError or FileNotFoundError for file {plugins_objects}'])                

        return None

