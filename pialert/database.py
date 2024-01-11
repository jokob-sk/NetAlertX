""" all things database to support Pi.Alert """

import sqlite3

# pialert modules
from const import fullDbPath, sql_devices_stats, sql_devices_all

from logger import mylog
from helper import json_obj, initOrSetParam, row_to_json, timeNowTZ #, updateState



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

        mylog('none', '[Database] Opening DB' )
        # Open DB and Cursor
        try:
            self.sql_connection = sqlite3.connect (fullDbPath, isolation_level=None)
            self.sql_connection.execute('pragma journal_mode=wal') #
            self.sql_connection.text_factory = str
            self.sql_connection.row_factory = sqlite3.Row
            self.sql = self.sql_connection.cursor()
        except sqlite3.Error as e:
            mylog('none',[ '[Database] - Open DB Error: ', e])


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

        # indicates, if Online_History table is available
        onlineHistoryAvailable = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='Online_History';
        """).fetchall() != []

        # Check if it is incompatible (Check if table has all required columns)
        isIncompatible = False

        if onlineHistoryAvailable :
          isIncompatible = self.sql.execute ("""
          SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Online_History') WHERE name='Archived_Devices'
          """).fetchone()[0] == 0

        # Drop table if available, but incompatible
        if onlineHistoryAvailable and isIncompatible:
          mylog('none','[upgradeDB] Table is incompatible, Dropping the Online_History table')
          self.sql.execute("DROP TABLE Online_History;")
          onlineHistoryAvailable = False

        if onlineHistoryAvailable == False :
          self.sql.execute("""
          CREATE TABLE "Online_History" (
            "Index"	INTEGER,
            "Scan_Date"	TEXT,
            "Online_Devices"	INTEGER,
            "Down_Devices"	INTEGER,
            "All_Devices"	INTEGER,
            "Archived_Devices" INTEGER,
            PRIMARY KEY("Index" AUTOINCREMENT)
          );
          """)

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


        # -------------------------------------------------------------------------
        # Settings table setup
        # -------------------------------------------------------------------------

        
        # Re-creating Settings table
        mylog('verbose', ["[upgradeDB] Re-creating Settings table"])

        self.sql.execute(""" DROP TABLE IF EXISTS Settings;""")
        self.sql.execute("""
            CREATE TABLE "Settings" (
            "Code_Name"	    TEXT,
            "Display_Name"	TEXT,
            "Description"	TEXT,
            "Type"          TEXT,
            "Options"       TEXT,
            "RegEx"         TEXT,
            "Value"	        TEXT,
            "Group"	        TEXT,
            "Events"	    TEXT
            );
            """)


        # -------------------------------------------------------------------------
        # Pholus_Scan table setup
        # -------------------------------------------------------------------------

        # Create Pholus_Scan table if missing
        mylog('verbose', ["[upgradeDB] Re-creating Pholus_Scan table"])
        self.sql.execute("""CREATE TABLE IF NOT EXISTS "Pholus_Scan" (
            "Index"	          INTEGER,
            "Info"	          TEXT,
            "Time"	          TEXT,
            "MAC"	          TEXT,
            "IP_v4_or_v6"	  TEXT,
            "Record_Type"	  TEXT,
            "Value"           TEXT,
            "Extra"           TEXT,
            PRIMARY KEY("Index" AUTOINCREMENT)
        );
        """)


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
        # Nmap_Scan table setup DEPRECATED after 1/1/2024
        # -------------------------------------------------------------------------

        # indicates, if Nmap_Scan table is available
        nmapScanMissing = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='Nmap_Scan';
        """).fetchone() == None

        if nmapScanMissing == False:
            # move data into the PLugins_Objects table
            self.sql.execute("""INSERT INTO Plugins_Objects (
                                    Plugin,
                                    Object_PrimaryID,
                                    Object_SecondaryID,
  									DateTimeCreated,
									DateTimeChanged,
                                    Watched_Value1,
                                    Watched_Value2,
                                    Watched_Value3,
                                    Watched_Value4,
                                    Status,
                                    Extra,
                                    UserData,
                                    ForeignKey
                                )
                                SELECT
                                    'NMAP' AS Plugin,
                                    MAC AS Object_PrimaryID,
                                    Port AS Object_SecondaryID,
									Time AS DateTimeCreated,
									DATETIME('now') AS DateTimeChanged,
                                    State AS Watched_Value1,
                                    Service AS Watched_Value2,
                                    '' AS Watched_Value3,
                                    '' AS Watched_Value4,
                                    'watched-not-changed' AS Status,
                                    Extra AS Extra,
                                    Extra AS UserData,
                                    MAC AS ForeignKey
                                FROM Nmap_Scan;""")

            # Delete the Nmap_Scan table
            self.sql.execute("DROP TABLE Nmap_Scan;")
            nmapScanMissing = True

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
        self.sql.execute("DROP TABLE IF EXISTS CurrentScan;")
        self.sql.execute(""" CREATE TABLE CurrentScan (                                
                                cur_MAC STRING(50) NOT NULL COLLATE NOCASE,
                                cur_IP STRING(50) NOT NULL COLLATE NOCASE,
                                cur_Vendor STRING(250),
                                cur_ScanMethod STRING(10),
                                cur_Name STRING(250),
                                cur_LastQuery STRING(250),
                                cur_DateTime STRING(250)
                            );
                        """)

        # -------------------------------------------------------------------------
        #  DELETING OBSOLETE TABLES - to remove with updated db file after 1/1/2024
        # -------------------------------------------------------------------------        

        # Deletes obsolete ScanCycles
        self.sql.execute(""" DROP TABLE IF EXISTS ScanCycles;""")
        self.sql.execute(""" DROP TABLE IF EXISTS DHCP_Leases;""")
        self.sql.execute(""" DROP TABLE IF EXISTS PiHole_Network;""")

        self.commitDB()

        # -------------------------------------------------------------------------
        #  DELETING OBSOLETE TABLES - to remove with updated db file after 1/1/2024
        # -------------------------------------------------------------------------


    #-------------------------------------------------------------------------------
    def get_table_as_json(self, sqlQuery):

        # mylog('debug',[ '[Database] - get_table_as_json - Query: ', sqlQuery])
        try:
            self.sql.execute(sqlQuery)
            columnNames = list(map(lambda x: x[0], self.sql.description))
            rows = self.sql.fetchall()
        except sqlite3.Error as e:
            mylog('none',[ '[Database] - SQL ERROR: ', e])
            return json_obj({}, []) # return empty object

        result = {"data":[]}
        for row in rows:
            tmp = row_to_json(columnNames, row)
            result["data"].append(tmp)

        # mylog('debug',[ '[Database] - get_table_as_json - returning ', len(rows), " rows with columns: ", columnNames])
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
            mylog('none',[ '[Database] - ERROR: inconsistent query and/or arguments.', query, " params: ", args])
        except sqlite3.Error as e:
            mylog('none',[ '[Database] - SQL ERROR: ', e])
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
            mylog('none',[ '[Database] - Warning!: query returns multiple rows, only first row is passed on!', query, " params: ", args])
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

#-------------------------------------------------------------------------------
def insertOnlineHistory(db):
    sql = db.sql #TO-DO
    startTime = timeNowTZ()
    # Add to History

    History_All = db.read("SELECT * FROM Devices")
    History_All_Devices  = len(History_All)

    History_Archived = db.read("SELECT * FROM Devices WHERE dev_Archived = 1")
    History_Archived_Devices  = len(History_Archived)

    History_Online = db.read("SELECT * FROM Devices WHERE dev_PresentLastScan = 1")
    History_Online_Devices  = len(History_Online)
    History_Offline_Devices = History_All_Devices - History_Archived_Devices - History_Online_Devices

    sql.execute ("INSERT INTO Online_History (Scan_Date, Online_Devices, Down_Devices, All_Devices, Archived_Devices) "+
                 "VALUES ( ?, ?, ?, ?, ?)", (startTime, History_Online_Devices, History_Offline_Devices, History_All_Devices, History_Archived_Devices ) )
    db.commitDB()