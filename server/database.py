""" all things database to support NetAlertX """

import sqlite3
import base64
import json

# Register NetAlertX modules 
from const import fullDbPath, sql_devices_stats, sql_devices_all, sql_generateGuid

from logger import mylog
from helper import json_obj, initOrSetParam, row_to_json, timeNowTZ#, split_string #, updateState
from appevent import AppEvent_obj

class DB():
    """
    DB Class to provide the basic database interactions.
    Open / Commit / Close / read / write
    """

    def __init__(self):
        self.sql = None
        self.sql_connection = None

    #-------------------------------------------------------------------------------
    def open (self):
        # Check if DB is open
        if self.sql_connection != None :
            mylog('debug','openDB: database already open')
            return

        mylog('verbose', '[Database] Opening DB' )
        # Open DB and Cursor
        try:
            self.sql_connection = sqlite3.connect (fullDbPath, isolation_level=None)
            self.sql_connection.execute('pragma journal_mode=wal') #
            self.sql_connection.text_factory = str
            self.sql_connection.row_factory = sqlite3.Row
            self.sql = self.sql_connection.cursor()
        except sqlite3.Error as e:
            mylog('verbose',[ '[Database] - Open DB Error: ', e])


    #-------------------------------------------------------------------------------
    def commitDB (self):
        if self.sql_connection == None :
            mylog('debug','commitDB: database is not open')
            return False

        # Commit changes to DB
        self.sql_connection.commit()
        return True

    #-------------------------------------------------------------------------------
    def rollbackDB(self):
        if self.sql_connection:
            self.sql_connection.rollback()

    #-------------------------------------------------------------------------------    
    def get_sql_array(self, query):
        if self.sql_connection == None :
            mylog('debug','getQueryArray: database is not open')
            return

        self.sql.execute(query)
        rows = self.sql.fetchall()
        #self.commitDB()

        #  convert result into list of lists
        arr = []
        for row in rows:
            r_temp = []
            for column in row:
                r_temp.append(column)
            arr.append(r_temp)

        return arr


    #-------------------------------------------------------------------------------
    def upgradeDB(self):
        """
        Check the current tables in the DB and upgrade them if neccessary
        """
  
        self.sql.execute("""
          CREATE TABLE IF NOT EXISTS "Online_History" (
            "Index"	INTEGER,
            "Scan_Date"	TEXT,
            "Online_Devices"	INTEGER,
            "Down_Devices"	INTEGER,
            "All_Devices"	INTEGER,
            "Archived_Devices" INTEGER,
            "Offline_Devices" INTEGER,
            PRIMARY KEY("Index" AUTOINCREMENT)
          );
          """)

        # -------------------------------------------------------------------  
        # DevicesNew - cleanup after 6/6/2025 - need to update also DB in the source code!
        
        # check if migration already done based on devMac
        devMac_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='devMac'
          """).fetchone()[0] == 0
        
        if devMac_missing:

          # -------------------------------------------------------------------------
          # Alter Devices table       
          # -------------------------------------------------------------------------
          # dev_Network_Node_MAC_ADDR column
          dev_Network_Node_MAC_ADDR_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_MAC_ADDR'
            """).fetchone()[0] == 0

          if dev_Network_Node_MAC_ADDR_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_Network_Node_MAC_ADDR to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_Network_Node_MAC_ADDR" TEXT
            """)

          # dev_Network_Node_port column
          dev_Network_Node_port_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_port'
            """).fetchone()[0] == 0

          if dev_Network_Node_port_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_Network_Node_port to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_Network_Node_port" INTEGER
            """)

          # dev_Icon column
          dev_Icon_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Icon'
            """).fetchone()[0] == 0

          if dev_Icon_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_Icon to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_Icon" TEXT
            """)

          # dev_GUID column
          dev_GUID_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_GUID'
            """).fetchone()[0] == 0

          if dev_GUID_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_GUID to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_GUID" TEXT
            """)

          # dev_NetworkSite column
          dev_NetworkSite_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_NetworkSite'
            """).fetchone()[0] == 0

          if dev_NetworkSite_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_NetworkSite to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_NetworkSite" TEXT
            """)

          # dev_SSID column
          dev_SSID_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_SSID'
            """).fetchone()[0] == 0

          if dev_SSID_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_SSID to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_SSID" TEXT
            """)

          # SQL query to update missing dev_GUID
          self.sql.execute(f'''
              UPDATE Devices
              SET dev_GUID = {sql_generateGuid}
              WHERE dev_GUID IS NULL
          ''')

          # dev_SyncHubNodeName column
          dev_SyncHubNodeName_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_SyncHubNodeName'
            """).fetchone()[0] == 0

          if dev_SyncHubNodeName_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_SyncHubNodeName to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_SyncHubNodeName" TEXT
            """)
            
          # dev_SourcePlugin column
          dev_SourcePlugin_missing = self.sql.execute ("""
              SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_SourcePlugin'
            """).fetchone()[0] == 0

          if dev_SourcePlugin_missing :
            mylog('verbose', ["[upgradeDB] Adding dev_SourcePlugin to the Devices table"])
            self.sql.execute("""
              ALTER TABLE "Devices" ADD "dev_SourcePlugin" TEXT
            """)
        
          # SQL to create Devices table with indexes
          sql_create_devices_new_tmp = """
          CREATE TABLE IF NOT EXISTS Devices_tmp (
              devMac STRING (50) PRIMARY KEY NOT NULL COLLATE NOCASE,
              devName STRING (50) NOT NULL DEFAULT "(unknown)",
              devOwner STRING (30) DEFAULT "(unknown)" NOT NULL,
              devType STRING (30),
              devVendor STRING (250),
              devFavorite BOOLEAN CHECK (devFavorite IN (0, 1)) DEFAULT (0) NOT NULL,
              devGroup STRING (10),
              devComments TEXT,
              devFirstConnection DATETIME NOT NULL,
              devLastConnection DATETIME NOT NULL,
              devLastIP STRING (50) NOT NULL COLLATE NOCASE,
              devStaticIP BOOLEAN DEFAULT (0) NOT NULL CHECK (devStaticIP IN (0, 1)),
              devScan INTEGER DEFAULT (1) NOT NULL,
              devLogEvents BOOLEAN NOT NULL DEFAULT (1) CHECK (devLogEvents IN (0, 1)),
              devAlertEvents BOOLEAN NOT NULL DEFAULT (1) CHECK (devAlertEvents IN (0, 1)),
              devAlertDown BOOLEAN NOT NULL DEFAULT (0) CHECK (devAlertDown IN (0, 1)),
              devSkipRepeated INTEGER DEFAULT 0 NOT NULL,
              devLastNotification DATETIME,
              devPresentLastScan BOOLEAN NOT NULL DEFAULT (0) CHECK (devPresentLastScan IN (0, 1)),
              devIsNew BOOLEAN NOT NULL DEFAULT (1) CHECK (devIsNew IN (0, 1)),
              devLocation STRING (250) COLLATE NOCASE,
              devIsArchived BOOLEAN NOT NULL DEFAULT (0) CHECK (devIsArchived IN (0, 1)),
              devParentMAC TEXT,
              devParentPort INTEGER,
              devIcon TEXT,
              devGUID TEXT,
              devSite TEXT,
              devSSID TEXT,
              devSyncHubNode TEXT,
              devSourcePlugin TEXT
          );

          CREATE INDEX IF NOT EXISTS IDX_dev_PresentLastScan ON Devices_tmp (devPresentLastScan);
          CREATE INDEX IF NOT EXISTS IDX_dev_FirstConnection ON Devices_tmp (devFirstConnection);
          CREATE INDEX IF NOT EXISTS IDX_dev_AlertDeviceDown ON Devices_tmp (devAlertDown);
          CREATE INDEX IF NOT EXISTS IDX_dev_StaticIP ON Devices_tmp (devStaticIP);
          CREATE INDEX IF NOT EXISTS IDX_dev_ScanCycle ON Devices_tmp (devScan);
          CREATE INDEX IF NOT EXISTS IDX_dev_Favorite ON Devices_tmp (devFavorite);
          CREATE INDEX IF NOT EXISTS IDX_dev_LastIP ON Devices_tmp (devLastIP);
          CREATE INDEX IF NOT EXISTS IDX_dev_NewDevice ON Devices_tmp (devIsNew);
          CREATE INDEX IF NOT EXISTS IDX_dev_Archived ON Devices_tmp (devIsArchived);
          """

          # Execute the creation of the Devices table and indexes
          self.sql.executescript(sql_create_devices_new_tmp)
          
          
          # copy over data
          sql_copy_from_devices = """
            INSERT OR IGNORE INTO Devices_tmp (
                devMac,
                devName,
                devOwner,
                devType,
                devVendor,
                devFavorite,
                devGroup,
                devComments,
                devFirstConnection,
                devLastConnection,
                devLastIP,
                devStaticIP,
                devScan,
                devLogEvents,
                devAlertEvents,
                devAlertDown,
                devSkipRepeated,
                devLastNotification,
                devPresentLastScan,
                devIsNew,
                devLocation,
                devIsArchived,
                devParentMAC,
                devParentPort,
                devIcon,
                devGUID,
                devSite,
                devSSID,
                devSyncHubNode,
                devSourcePlugin
            )
            SELECT
                dev_MAC AS devMac,
                dev_Name AS devName,
                dev_Owner AS devOwner,
                dev_DeviceType AS devType,
                dev_Vendor AS devVendor,
                dev_Favorite AS devFavorite,
                dev_Group AS devGroup,
                dev_Comments AS devComments,
                dev_FirstConnection AS devFirstConnection,
                dev_LastConnection AS devLastConnection,
                dev_LastIP AS devLastIP,
                dev_StaticIP AS devStaticIP,
                dev_ScanCycle AS devScan,
                dev_LogEvents AS devLogEvents,
                dev_AlertEvents AS devAlertEvents,
                dev_AlertDeviceDown AS devAlertDown,
                dev_SkipRepeated AS devSkipRepeated,
                dev_LastNotification AS devLastNotification,
                dev_PresentLastScan AS devPresentLastScan,
                dev_NewDevice AS devIsNew,
                dev_Location AS devLocation,
                dev_Archived AS devIsArchived,
                dev_Network_Node_MAC_ADDR AS devParentMAC,
                dev_Network_Node_port AS devParentPort,
                dev_Icon AS devIcon,
                dev_GUID AS devGUID,
                dev_NetworkSite AS devSite,
                dev_SSID AS devSSID,
                dev_SyncHubNodeName AS devSyncHubNode,
                dev_SourcePlugin AS devSourcePlugin
            FROM Devices;
          """
          
          self.sql.execute(sql_copy_from_devices)
          
          
          self.sql.execute(""" DROP TABLE Devices;""")
          # SQL to create Devices table with indexes
          sql_create_devices_new = """
          CREATE TABLE IF NOT EXISTS Devices (
              devMac STRING (50) PRIMARY KEY NOT NULL COLLATE NOCASE,
              devName STRING (50) NOT NULL DEFAULT "(unknown)",
              devOwner STRING (30) DEFAULT "(unknown)" NOT NULL,
              devType STRING (30),
              devVendor STRING (250),
              devFavorite BOOLEAN CHECK (devFavorite IN (0, 1)) DEFAULT (0) NOT NULL,
              devGroup STRING (10),
              devComments TEXT,
              devFirstConnection DATETIME NOT NULL,
              devLastConnection DATETIME NOT NULL,
              devLastIP STRING (50) NOT NULL COLLATE NOCASE,
              devStaticIP BOOLEAN DEFAULT (0) NOT NULL CHECK (devStaticIP IN (0, 1)),
              devScan INTEGER DEFAULT (1) NOT NULL,
              devLogEvents BOOLEAN NOT NULL DEFAULT (1) CHECK (devLogEvents IN (0, 1)),
              devAlertEvents BOOLEAN NOT NULL DEFAULT (1) CHECK (devAlertEvents IN (0, 1)),
              devAlertDown BOOLEAN NOT NULL DEFAULT (0) CHECK (devAlertDown IN (0, 1)),
              devSkipRepeated INTEGER DEFAULT 0 NOT NULL,
              devLastNotification DATETIME,
              devPresentLastScan BOOLEAN NOT NULL DEFAULT (0) CHECK (devPresentLastScan IN (0, 1)),
              devIsNew BOOLEAN NOT NULL DEFAULT (1) CHECK (devIsNew IN (0, 1)),
              devLocation STRING (250) COLLATE NOCASE,
              devIsArchived BOOLEAN NOT NULL DEFAULT (0) CHECK (devIsArchived IN (0, 1)),
              devParentMAC TEXT,
              devParentPort INTEGER,
              devIcon TEXT,
              devGUID TEXT,
              devSite TEXT,
              devSSID TEXT,
              devSyncHubNode TEXT,
              devSourcePlugin TEXT
          );

          CREATE INDEX IF NOT EXISTS IDX_dev_PresentLastScan ON Devices (devPresentLastScan);
          CREATE INDEX IF NOT EXISTS IDX_dev_FirstConnection ON Devices (devFirstConnection);
          CREATE INDEX IF NOT EXISTS IDX_dev_AlertDeviceDown ON Devices (devAlertDown);
          CREATE INDEX IF NOT EXISTS IDX_dev_StaticIP ON Devices (devStaticIP);
          CREATE INDEX IF NOT EXISTS IDX_dev_ScanCycle ON Devices (devScan);
          CREATE INDEX IF NOT EXISTS IDX_dev_Favorite ON Devices (devFavorite);
          CREATE INDEX IF NOT EXISTS IDX_dev_LastIP ON Devices (devLastIP);
          CREATE INDEX IF NOT EXISTS IDX_dev_NewDevice ON Devices (devIsNew);
          CREATE INDEX IF NOT EXISTS IDX_dev_Archived ON Devices (devIsArchived);
          """

          # Execute the creation of the Devices table and indexes
          self.sql.executescript(sql_create_devices_new)
          
          # copy over data
          sql_copy_from_devices_tmp = """
            INSERT OR IGNORE INTO Devices (
                devMac,
                devName,
                devOwner,
                devType,
                devVendor,
                devFavorite,
                devGroup,
                devComments,
                devFirstConnection,
                devLastConnection,
                devLastIP,
                devStaticIP,
                devScan,
                devLogEvents,
                devAlertEvents,
                devAlertDown,
                devSkipRepeated,
                devLastNotification,
                devPresentLastScan,
                devIsNew,
                devLocation,
                devIsArchived,
                devParentMAC,
                devParentPort,
                devIcon,
                devGUID,
                devSite,
                devSSID,
                devSyncHubNode,
                devSourcePlugin
            )
            SELECT
                devMac,
                devName,
                devOwner,
                devType,
                devVendor,
                devFavorite,
                devGroup,
                devComments,
                devFirstConnection,
                devLastConnection,
                devLastIP,
                devStaticIP,
                devScan,
                devLogEvents,
                devAlertEvents,
                devAlertDown,
                devSkipRepeated,
                devLastNotification,
                devPresentLastScan,
                devIsNew,
                devLocation,
                devIsArchived,
                devParentMAC,
                devParentPort,
                devIcon,
                devGUID,
                devSite,
                devSSID,
                devSyncHubNode,
                devSourcePlugin
            FROM Devices_tmp;
          """
          
          self.sql.execute(sql_copy_from_devices_tmp)
          self.sql.execute(""" DROP TABLE Devices_tmp;""")
        
        
        # VIEWS
        
        self.sql.execute(""" DROP VIEW IF EXISTS Events_Devices;""")
        self.sql.execute(""" CREATE VIEW Events_Devices AS 
                            SELECT * 
                            FROM Events 
                            LEFT JOIN Devices ON eve_MAC = devMac;
                          """)
        
        
        self.sql.execute(""" DROP VIEW IF EXISTS LatestEventsPerMAC;""")
        self.sql.execute("""CREATE VIEW LatestEventsPerMAC AS
                                WITH RankedEvents AS (
                                    SELECT 
                                        e.*,
                                        ROW_NUMBER() OVER (PARTITION BY e.eve_MAC ORDER BY e.eve_DateTime DESC) AS row_num
                                    FROM Events AS e
                                )
                                SELECT 
                                    e.*, 
                                    d.*, 
                                    c.*
                                FROM RankedEvents AS e
                                LEFT JOIN Devices AS d ON e.eve_MAC = d.devMac
                                INNER JOIN CurrentScan AS c ON e.eve_MAC = c.cur_MAC
                                WHERE e.row_num = 1;""")
        
        self.sql.execute(""" DROP VIEW IF EXISTS Sessions_Devices;""")
        self.sql.execute("""CREATE VIEW Sessions_Devices AS SELECT * FROM Sessions LEFT JOIN "Devices" ON ses_MAC = devMac;""")
        
        # -------------------------------------------------------------------------
        # Settings table setup
        # -------------------------------------------------------------------------

        
        # Re-creating Settings table
        mylog('verbose', ["[upgradeDB] Re-creating Settings table"])

        self.sql.execute(""" DROP TABLE IF EXISTS Settings;""")
        self.sql.execute("""
            CREATE TABLE "Settings" (
            "Code_Name"	      TEXT,
            "Display_Name"	  TEXT,
            "Description"	    TEXT,
            "Type"            TEXT,
            "Options"         TEXT,
            "RegEx"           TEXT,
            "Group"	          TEXT,
            "Value"	          TEXT,
            "Events"	        TEXT,
            "OverriddenByEnv" INTEGER
            );
            """)


        # Create Pholus_Scan table if missing
        mylog('verbose', ["[upgradeDB] Removing Pholus_Scan table"])
        self.sql.execute("""DROP TABLE IF EXISTS Pholus_Scan""")


        # -------------------------------------------------------------------------
        # Parameters table setup
        # -------------------------------------------------------------------------

        # Re-creating Parameters table
        mylog('verbose', ["[upgradeDB] Re-creating Parameters table"])
        self.sql.execute("DROP TABLE Parameters;")

        self.sql.execute("""
          CREATE TABLE "Parameters" (
            "par_ID" TEXT PRIMARY KEY,
            "par_Value"	TEXT
          );
          """)        
       

        # -------------------------------------------------------------------------
        # Plugins tables setup
        # -------------------------------------------------------------------------

        # Plugin state
        sql_Plugins_Objects = """ CREATE TABLE IF NOT EXISTS Plugins_Objects(
                                    "Index"	          INTEGER,
                                    Plugin TEXT NOT NULL,
                                    Object_PrimaryID TEXT NOT NULL,
                                    Object_SecondaryID TEXT NOT NULL,
                                    DateTimeCreated TEXT NOT NULL,
                                    DateTimeChanged TEXT NOT NULL,
                                    Watched_Value1 TEXT NOT NULL,
                                    Watched_Value2 TEXT NOT NULL,
                                    Watched_Value3 TEXT NOT NULL,
                                    Watched_Value4 TEXT NOT NULL,
                                    Status TEXT NOT NULL,
                                    Extra TEXT NOT NULL,
                                    UserData TEXT NOT NULL,
                                    ForeignKey TEXT NOT NULL,
                                    SyncHubNodeName TEXT,
                                    "HelpVal1" TEXT,
                                    "HelpVal2" TEXT,
                                    "HelpVal3" TEXT,
                                    "HelpVal4" TEXT,
                                    PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """
        self.sql.execute(sql_Plugins_Objects)

        # -----------------------------------------
        # REMOVE after 6/6/2025 - START
        # -----------------------------------------
        # syncHubNodeName column
        plug_SyncHubNodeName_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Plugins_Objects') WHERE name='SyncHubNodeName'
          """).fetchone()[0] == 0

        if plug_SyncHubNodeName_missing :
          mylog('verbose', ["[upgradeDB] Adding SyncHubNodeName to the Plugins_Objects table"])
          self.sql.execute("""
            ALTER TABLE "Plugins_Objects" ADD "SyncHubNodeName" TEXT
          """)
          
        # helper columns HelpVal1-4
        plug_HelpValues_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Plugins_Objects') WHERE name='HelpVal1'
          """).fetchone()[0] == 0

        if plug_HelpValues_missing :
          mylog('verbose', ["[upgradeDB] Adding HelpVal1-4 to the Plugins_Objects table"])
          self.sql.execute('ALTER TABLE "Plugins_Objects" ADD COLUMN "HelpVal1" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_Objects" ADD COLUMN "HelpVal2" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_Objects" ADD COLUMN "HelpVal3" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_Objects" ADD COLUMN "HelpVal4" TEXT')
          
        # -----------------------------------------
        # REMOVE after 6/6/2025 - END
        # -----------------------------------------

        # Plugin execution results
        sql_Plugins_Events = """ CREATE TABLE IF NOT EXISTS Plugins_Events(
                                    "Index"	          INTEGER,
                                    Plugin TEXT NOT NULL,
                                    Object_PrimaryID TEXT NOT NULL,
                                    Object_SecondaryID TEXT NOT NULL,
                                    DateTimeCreated TEXT NOT NULL,
                                    DateTimeChanged TEXT NOT NULL,
                                    Watched_Value1 TEXT NOT NULL,
                                    Watched_Value2 TEXT NOT NULL,
                                    Watched_Value3 TEXT NOT NULL,
                                    Watched_Value4 TEXT NOT NULL,
                                    Status TEXT NOT NULL,
                                    Extra TEXT NOT NULL,
                                    UserData TEXT NOT NULL,
                                    ForeignKey TEXT NOT NULL,
                                    SyncHubNodeName TEXT,
                                    "HelpVal1" TEXT,
                                    "HelpVal2" TEXT,
                                    "HelpVal3" TEXT,
                                    "HelpVal4" TEXT,
                                    PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """
        self.sql.execute(sql_Plugins_Events)

        # -----------------------------------------
        # REMOVE after 6/6/2025 - START
        # -----------------------------------------
        
        # syncHubNodeName column
        plug_SyncHubNodeName_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Plugins_Events') WHERE name='SyncHubNodeName'
          """).fetchone()[0] == 0

        if plug_SyncHubNodeName_missing :
          mylog('verbose', ["[upgradeDB] Adding SyncHubNodeName to the Plugins_Events table"])
          self.sql.execute("""
            ALTER TABLE "Plugins_Events" ADD "SyncHubNodeName" TEXT
          """)
          
        # helper columns HelpVal1-4
        plug_HelpValues_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Plugins_Events') WHERE name='HelpVal1'
          """).fetchone()[0] == 0

        if plug_HelpValues_missing :
          mylog('verbose', ["[upgradeDB] Adding HelpVal1-4 to the Plugins_Events table"])
          self.sql.execute('ALTER TABLE "Plugins_Events" ADD COLUMN "HelpVal1" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_Events" ADD COLUMN "HelpVal2" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_Events" ADD COLUMN "HelpVal3" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_Events" ADD COLUMN "HelpVal4" TEXT')
          
        # -----------------------------------------
        # REMOVE after 6/6/2025 - END
        # -----------------------------------------


        # Plugin execution history
        sql_Plugins_History = """ CREATE TABLE IF NOT EXISTS Plugins_History(
                                    "Index"	          INTEGER,
                                    Plugin TEXT NOT NULL,
                                    Object_PrimaryID TEXT NOT NULL,
                                    Object_SecondaryID TEXT NOT NULL,
                                    DateTimeCreated TEXT NOT NULL,
                                    DateTimeChanged TEXT NOT NULL,
                                    Watched_Value1 TEXT NOT NULL,
                                    Watched_Value2 TEXT NOT NULL,
                                    Watched_Value3 TEXT NOT NULL,
                                    Watched_Value4 TEXT NOT NULL,
                                    Status TEXT NOT NULL,
                                    Extra TEXT NOT NULL,
                                    UserData TEXT NOT NULL,
                                    ForeignKey TEXT NOT NULL,
                                    SyncHubNodeName TEXT,
                                    "HelpVal1" TEXT,
                                    "HelpVal2" TEXT,
                                    "HelpVal3" TEXT,
                                    "HelpVal4" TEXT,
                                    PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """
        self.sql.execute(sql_Plugins_History)
        
        # -----------------------------------------
        # REMOVE after 6/6/2025 - START
        # -----------------------------------------

        # syncHubNodeName column
        plug_SyncHubNodeName_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Plugins_History') WHERE name='SyncHubNodeName'
          """).fetchone()[0] == 0

        if plug_SyncHubNodeName_missing :
          mylog('verbose', ["[upgradeDB] Adding SyncHubNodeName to the Plugins_History table"])
          self.sql.execute("""
            ALTER TABLE "Plugins_History" ADD "SyncHubNodeName" TEXT
          """)
          
        # helper columns HelpVal1-4
        plug_HelpValues_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Plugins_History') WHERE name='HelpVal1'
          """).fetchone()[0] == 0

        if plug_HelpValues_missing :
          mylog('verbose', ["[upgradeDB] Adding HelpVal1-4 to the Plugins_History table"])
          self.sql.execute('ALTER TABLE "Plugins_History" ADD COLUMN "HelpVal1" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_History" ADD COLUMN "HelpVal2" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_History" ADD COLUMN "HelpVal3" TEXT')
          self.sql.execute('ALTER TABLE "Plugins_History" ADD COLUMN "HelpVal4" TEXT')

        # -----------------------------------------
        # REMOVE after 6/6/2025 - END
        # -----------------------------------------

        # -------------------------------------------------------------------------
        # Plugins_Language_Strings table setup
        # -------------------------------------------------------------------------

        # Dynamically generated language strings
        self.sql.execute("DROP TABLE IF EXISTS Plugins_Language_Strings;")
        self.sql.execute(""" CREATE TABLE IF NOT EXISTS Plugins_Language_Strings(
                                "Index"	          INTEGER,
                                Language_Code TEXT NOT NULL,
                                String_Key TEXT NOT NULL,
                                String_Value TEXT NOT NULL,
                                Extra TEXT NOT NULL,
                                PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """)

        self.commitDB()        

 

        # -------------------------------------------------------------------------
        # CurrentScan table setup
        # -------------------------------------------------------------------------

        # indicates, if CurrentScan table is available
        # 🐛 CurrentScan DEBUG: comment out below when debugging to keep the CurrentScan table after restarts/scan finishes
        self.sql.execute("DROP TABLE IF EXISTS CurrentScan;")
        self.sql.execute(""" CREATE TABLE IF NOT EXISTS CurrentScan (                                
                                cur_MAC STRING(50) NOT NULL COLLATE NOCASE,
                                cur_IP STRING(50) NOT NULL COLLATE NOCASE,
                                cur_Vendor STRING(250),
                                cur_ScanMethod STRING(10),
                                cur_Name STRING(250),
                                cur_LastQuery STRING(250),
                                cur_DateTime STRING(250),
                                cur_SyncHubNodeName STRING(50),
                                cur_NetworkSite STRING(250),
                                cur_SSID STRING(250),
                                cur_NetworkNodeMAC STRING(250),
                                cur_PORT STRING(250),
                                cur_Type STRING(250),
                                UNIQUE(cur_MAC)
                            );
                        """)

        self.commitDB()        

        # -------------------------------------------------------------------------
        # Create the LatestEventsPerMAC view
        # -------------------------------------------------------------------------

        # Dynamically generated language strings
        self.sql.execute(""" CREATE VIEW IF NOT EXISTS LatestEventsPerMAC AS
                                WITH RankedEvents AS (
                                    SELECT 
                                        e.*,
                                        ROW_NUMBER() OVER (PARTITION BY e.eve_MAC ORDER BY e.eve_DateTime DESC) AS row_num
                                    FROM Events AS e
                                )
                                SELECT 
                                    e.*, 
                                    d.*, 
                                    c.*
                                FROM RankedEvents AS e
                                LEFT JOIN Devices AS d ON e.eve_MAC = d.devMac
                                INNER JOIN CurrentScan AS c ON e.eve_MAC = c.cur_MAC
                                WHERE e.row_num = 1;
                            """)

        # handling the Convert_Events_to_Sessions / Sessions screens         
        self.sql.execute("""DROP VIEW IF EXISTS Convert_Events_to_Sessions;""")
        self.sql.execute("""CREATE VIEW Convert_Events_to_Sessions AS  SELECT EVE1.eve_MAC,
                                      EVE1.eve_IP,
                                      EVE1.eve_EventType AS eve_EventTypeConnection,
                                      EVE1.eve_DateTime AS eve_DateTimeConnection,
                                      CASE WHEN EVE2.eve_EventType IN ('Disconnected', 'Device Down') OR
                                                EVE2.eve_EventType IS NULL THEN EVE2.eve_EventType ELSE '<missing event>' END AS eve_EventTypeDisconnection,
                                      CASE WHEN EVE2.eve_EventType IN ('Disconnected', 'Device Down') THEN EVE2.eve_DateTime ELSE NULL END AS eve_DateTimeDisconnection,
                                      CASE WHEN EVE2.eve_EventType IS NULL THEN 1 ELSE 0 END AS eve_StillConnected,
                                      EVE1.eve_AdditionalInfo
                                  FROM Events AS EVE1
                                      LEFT JOIN
                                      Events AS EVE2 ON EVE1.eve_PairEventRowID = EVE2.RowID
                                WHERE EVE1.eve_EventType IN ('New Device', 'Connected','Down Reconnected')
                            UNION
                                SELECT eve_MAC,
                                      eve_IP,
                                      '<missing event>' AS eve_EventTypeConnection,
                                      NULL AS eve_DateTimeConnection,
                                      eve_EventType AS eve_EventTypeDisconnection,
                                      eve_DateTime AS eve_DateTimeDisconnection,
                                      0 AS eve_StillConnected,
                                      eve_AdditionalInfo
                                  FROM Events AS EVE1
                                WHERE (eve_EventType = 'Device Down' OR
                                        eve_EventType = 'Disconnected') AND
                                      EVE1.eve_PairEventRowID IS NULL;
                          """)

        self.commitDB()     
        
        # Init the AppEvent database table
        AppEvent_obj(self)

        # -------------------------------------------------------------------------
        #  DELETING OBSOLETE TABLES - to remove with updated db file after 9/9/2024
        # -------------------------------------------------------------------------        

        # Deletes obsolete ScanCycles
        self.sql.execute(""" DROP TABLE IF EXISTS ScanCycles;""")
        self.sql.execute(""" DROP TABLE IF EXISTS DHCP_Leases;""")
        self.sql.execute(""" DROP TABLE IF EXISTS PiHole_Network;""")

        self.commitDB()

        # -------------------------------------------------------------------------
        #  DELETING OBSOLETE TABLES - to remove with updated db file after 9/9/2024
        # -------------------------------------------------------------------------


    #-------------------------------------------------------------------------------
    def get_table_as_json(self, sqlQuery):

        # mylog('debug',[ '[Database] - get_table_as_json - Query: ', sqlQuery])
        try:
            self.sql.execute(sqlQuery)
            columnNames = list(map(lambda x: x[0], self.sql.description))
            rows = self.sql.fetchall()
        except sqlite3.Error as e:
            mylog('verbose',[ '[Database] - SQL ERROR: ', e])
            return json_obj({}, []) # return empty object

        result = {"data":[]}
        for row in rows:
            tmp = row_to_json(columnNames, row)
            result["data"].append(tmp)

        # mylog('debug',[ '[Database] - get_table_as_json - returning ', len(rows), " rows with columns: ", columnNames])
        # mylog('debug',[ '[Database] - get_table_as_json - returning json ', json.dumps(result) ])
        return json_obj(result, columnNames)

    #-------------------------------------------------------------------------------
    # referece from here: https://codereview.stackexchange.com/questions/241043/interface-class-for-sqlite-databases
    #-------------------------------------------------------------------------------
    def read(self, query, *args):
        """check the query and arguments are aligned and are read only"""
        # mylog('debug',[ '[Database] - Read All: SELECT Query: ', query, " params: ", args])
        try:
            assert query.count('?') == len(args)
            assert query.upper().strip().startswith('SELECT')
            self.sql.execute(query, args)
            rows = self.sql.fetchall()
            return rows
        except AssertionError:
            mylog('verbose',[ '[Database] - ERROR: inconsistent query and/or arguments.', query, " params: ", args])
        except sqlite3.Error as e:
            mylog('verbose',[ '[Database] - SQL ERROR: ', e])
        return None

    def read_one(self, query, *args):
        """ 
        call read() with the same arguments but only returns the first row.
        should only be used when there is a single row result expected
        """

        mylog('debug',[ '[Database] - Read One: ', query, " params: ", args])
        rows = self.read(query, *args)
        if len(rows) == 1:
            return rows[0]
                
        if len(rows) > 1: 
            mylog('verbose',[ '[Database] - Warning!: query returns multiple rows, only first row is passed on!', query, " params: ", args])
            return rows[0]
        # empty result set
        return None



#-------------------------------------------------------------------------------
def get_device_stats(db):
    # columns = ["online","down","all","archived","new","unknown"]
    return db.read_one(sql_devices_stats)
#-------------------------------------------------------------------------------
def get_all_devices(db):
    return db.read(sql_devices_all)

#-------------------------------------------------------------------------------

