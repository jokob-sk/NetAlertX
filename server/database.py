""" all things database to support NetAlertX """

import sqlite3
import base64
import json

# Register NetAlertX modules 
from const import fullDbPath, sql_devices_stats, sql_devices_all, sql_generateGuid

from logger import mylog
from helper import json_obj, initOrSetParam, row_to_json, timeNowTZ
from workflows.app_events import AppEvent_obj

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

        # -------------------------------------------------------------------------
        # Alter Devices table       
        # -------------------------------------------------------------------------
        
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


        # add fields if missing
            
        # devFQDN missing?
        devFQDN_missing = self.sql.execute ("""
            SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='devFQDN'
          """).fetchone()[0] == 0
        
        if devFQDN_missing:

          mylog('verbose', ["[upgradeDB] Adding devFQDN to the Devices table"])
          self.sql.execute("""
            ALTER TABLE "Devices" ADD "devFQDN" TEXT
          """)

        
        # -------------------------------------------------------------------------
        # Settings table setup
        # -------------------------------------------------------------------------

        
        # Re-creating Settings table
        mylog('verbose', ["[upgradeDB] Re-creating Settings table"])

        self.sql.execute(""" DROP TABLE IF EXISTS Settings;""")
        self.sql.execute("""
            CREATE TABLE "Settings" (
            "setKey"	        TEXT,
            "setName"	        TEXT,
            "setDescription"	TEXT,
            "setType"         TEXT,
            "setOptions"      TEXT,
            "setGroup"	          TEXT,
            "setValue"	      TEXT,
            "setEvents"	        TEXT,
            "setOverriddenByEnv" INTEGER
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
                                    ObjectGUID TEXT,
                                    PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """
        self.sql.execute(sql_Plugins_Objects)

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
   
def get_array_from_sql_rows(rows):
    # Convert result into list of lists
    arr = []
    for row in rows:
        if isinstance(row, sqlite3.Row):
            arr.append(list(row))  # Convert row to list
        elif isinstance(row, (tuple, list)):  
            arr.append(list(row))  # Already iterable, just convert to list
        else:
            arr.append([row])  # Handle single values safely

    return arr

#-------------------------------------------------------------------------------

