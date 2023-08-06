""" all things database to support Pi.Alert """

import sqlite3

# pialert modules
from const import fullDbPath, sql_devices_stats, sql_devices_all

from logger import mylog
from helper import json_struc, initOrSetParam, row_to_json, timeNowTZ #, updateState



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
            mylog('debug','openDB: databse already open')
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
            mylog('debug','commitDB: databse is not open')
            return False

        # Commit changes to DB
        self.sql_connection.commit()
        return True

    #-------------------------------------------------------------------------------
    def get_sql_array(self, query):
        if self.sql_connection == None :
            mylog('debug','getQueryArray: databse is not open')
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

    #===============================================================================
    # Cleanup / upkeep database
    #===============================================================================
    def cleanup_database (self, startTime, DAYS_TO_KEEP_EVENTS, PHOLUS_DAYS_DATA, HRS_TO_KEEP_NEWDEV, PLUGINS_KEEP_HIST):
        """
        Cleaning out old records from the tables that don't need to keep all data.
        """
        # Header
        #updateState(self,"Upkeep: Clean DB")
        mylog('verbose', ['[DB Cleanup] Upkeep Database:' ])

        # Cleanup Online History
        mylog('verbose', ['[DB Cleanup] Online_History: Delete all but keep latest 150 entries'])
        self.sql.execute ("""DELETE from Online_History where "Index" not in (
                             SELECT "Index" from Online_History 
                             order by Scan_Date desc limit 150)""")
        mylog('verbose', ['[DB Cleanup] Optimize Database'])
        # Cleanup Events
        mylog('verbose', [f'[DB Cleanup] Events: Delete all older than {str(DAYS_TO_KEEP_EVENTS)} days (DAYS_TO_KEEP_EVENTS setting)'])
        self.sql.execute (f"""DELETE FROM Events 
                             WHERE eve_DateTime <= date('now', '-{str(DAYS_TO_KEEP_EVENTS)} day')""")
                             
        # Cleanup Plugin Events History
        mylog('verbose', ['[DB Cleanup] Plugins_History: Delete all older than '+str(DAYS_TO_KEEP_EVENTS)+' days (DAYS_TO_KEEP_EVENTS setting)'])
        self.sql.execute (f"""DELETE FROM Plugins_History 
                             WHERE DateTimeChanged <= date('now', '{str(DAYS_TO_KEEP_EVENTS)} day')""")

        # Trim Plugins_History entries to less than PLUGINS_KEEP_HIST setting 
        mylog('verbose', [f'[DB Cleanup] Plugins_History: Trim Plugins_History entries to less than {str(PLUGINS_KEEP_HIST)} (PLUGINS_KEEP_HIST setting)'])
        self.sql.execute (f"""DELETE from Plugins_History where "Index" not in (
                        SELECT "Index" from Plugins_History 
                        order by "Index" desc limit {str(PLUGINS_KEEP_HIST)})""")

        # Cleanup Pholus_Scan
        if PHOLUS_DAYS_DATA != 0:
            mylog('verbose', ['[DB Cleanup] Pholus_Scan: Delete all older than ' + str(PHOLUS_DAYS_DATA) + ' days (PHOLUS_DAYS_DATA setting)'])
            # todo: improvement possibility: keep at least N per mac
            self.sql.execute (f"""DELETE FROM Pholus_Scan 
                                 WHERE Time <= date('now', '-{str(PHOLUS_DAYS_DATA)} day')""") 
        # Cleanup New Devices
        if HRS_TO_KEEP_NEWDEV != 0:
            mylog('verbose', [f'[DB Cleanup] Devices: Delete all New Devices older than {str(HRS_TO_KEEP_NEWDEV)} hours (HRS_TO_KEEP_NEWDEV setting)'])            
            self.sql.execute (f"""DELETE FROM Devices 
                                  WHERE dev_NewDevice = 1 AND dev_FirstConnection < date('now', '+{str(HRS_TO_KEEP_NEWDEV)} hour')""") 

        # De-Dupe (de-duplicate - remove duplicate entries) from the Pholus_Scan table
        mylog('verbose', ['[DB Cleanup] Pholus_Scan: Delete all duplicates'])
        self.sql.execute ("""DELETE  FROM Pholus_Scan
                        WHERE rowid > (
                        SELECT MIN(rowid) FROM Pholus_Scan p2
                        WHERE Pholus_Scan.MAC = p2.MAC
                        AND Pholus_Scan.Value = p2.Value
                        AND Pholus_Scan.Record_Type = p2.Record_Type
                        );""")
        # De-Dupe (de-duplicate - remove duplicate entries) from the Nmap_Scan table
        mylog('verbose', ['[DB Cleanup] Nmap_Scan: Delete all duplicates'])
        self.sql.execute ("""DELETE  FROM Nmap_Scan
                        WHERE rowid > (
                        SELECT MIN(rowid) FROM Nmap_Scan p2
                        WHERE Nmap_Scan.MAC = p2.MAC
                        AND Nmap_Scan.Port = p2.Port
                        AND Nmap_Scan.State = p2.State
                        AND Nmap_Scan.Service = p2.Service
                        );""")


        # Shrink DB
        mylog('verbose', ['[DB Cleanup] Shrink Database'])
        self.sql.execute ("VACUUM;")
        self.commitDB()

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

        # Alter Devices table
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

        # indicates, if Settings table is available
        settingsMissing = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='Settings';
        """).fetchone() == None

        # Re-creating Settings table
        mylog('verbose', ["[upgradeDB] Re-creating Settings table"])

        if settingsMissing == False:
            self.sql.execute("DROP TABLE Settings;")

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

        # indicates, if Pholus_Scan table is available
        pholusScanMissing = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='Pholus_Scan';
        """).fetchone() == None

        # if pholusScanMissing == False:
        #     # Re-creating Pholus_Scan table
        #     self.sql.execute("DROP TABLE Pholus_Scan;")
        #     pholusScanMissing = True

        if pholusScanMissing:
            mylog('verbose', ["[upgradeDB] Re-creating Pholus_Scan table"])
            self.sql.execute("""
            CREATE TABLE "Pholus_Scan" (
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

        # indicates, if Nmap_Scan table is available
        nmapScanMissing = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='Nmap_Scan';
        """).fetchone() == None

        # Re-creating Parameters table
        mylog('verbose', ["[upgradeDB] Re-creating Parameters table"])
        self.sql.execute("DROP TABLE Parameters;")

        self.sql.execute("""
          CREATE TABLE "Parameters" (
            "par_ID" TEXT PRIMARY KEY,
            "par_Value"	TEXT
          );
          """)

        # Initialize Parameters if unavailable
        initOrSetParam(self, 'Back_App_State','Initializing')

        # if nmapScanMissing == False:
        #     # Re-creating Nmap_Scan table
        #     self.sql.execute("DROP TABLE Nmap_Scan;")
        #     nmapScanMissing = True

        if nmapScanMissing:
            mylog('verbose', ["[upgradeDB] Re-creating Nmap_Scan table"])
            self.sql.execute("""
            CREATE TABLE "Nmap_Scan" (
            "Index"	          INTEGER,
            "MAC"	          TEXT,
            "Port"	          TEXT,
            "Time"	          TEXT,
            "State"	          TEXT,
            "Service"	      TEXT,
            "Extra"           TEXT,
            PRIMARY KEY("Index" AUTOINCREMENT)
            );
            """)

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

        # Dynamically generated language strings
        # indicates, if Language_Strings table is available
        languageStringsMissing = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='Plugins_Language_Strings';
        """).fetchone() == None

        if languageStringsMissing == False:
            self.sql.execute("DROP TABLE Plugins_Language_Strings;")

        self.sql.execute(""" CREATE TABLE IF NOT EXISTS Plugins_Language_Strings(
                            "Index"	          INTEGER,
                            Language_Code TEXT NOT NULL,
                            String_Key TEXT NOT NULL,
                            String_Value TEXT NOT NULL,
                            Extra TEXT NOT NULL,
                            PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """)

        self.commitDB()        
        
        # indicates, if CurrentScan table is available
        currentScanMissing = self.sql.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
        AND name='CurrentScan';
        """).fetchone() == None

        if currentScanMissing == False:
            self.sql.execute("DROP TABLE CurrentScan;")

        self.sql.execute(""" CREATE TABLE CurrentScan (
                                cur_ScanCycle INTEGER NOT NULL,
                                cur_MAC STRING(50) NOT NULL COLLATE NOCASE,
                                cur_IP STRING(50) NOT NULL COLLATE NOCASE,
                                cur_Vendor STRING(250),
                                cur_ScanMethod STRING(10)
                            );
                        """)

        self.commitDB()


    #-------------------------------------------------------------------------------
    def get_table_as_json(self, sqlQuery):

        mylog('debug',[ '[Database] - get_table_as_json - Query: ', sqlQuery])
        try:
            self.sql.execute(sqlQuery)
            columnNames = list(map(lambda x: x[0], self.sql.description))
            rows = self.sql.fetchall()
        except sqlite3.Error as e:
            mylog('none',[ '[Database] - SQL ERROR: ', e])
            return None

        result = {"data":[]}
        for row in rows:
            tmp = row_to_json(columnNames, row)
            result["data"].append(tmp)

        mylog('debug',[ '[Database] - get_table_as_json - returning ', len(rows), " rows with columns: ", columnNames])
        return json_struc(result, columnNames)

    #-------------------------------------------------------------------------------
    # referece from here: https://codereview.stackexchange.com/questions/241043/interface-class-for-sqlite-databases
    #-------------------------------------------------------------------------------
    def read(self, query, *args):
        """check the query and arguments are aligned and are read only"""
        mylog('debug',[ '[Database] - Read All: SELECT Query: ', query, " params: ", args])
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

    # only run this if the scans have run
    scanCount = db.read_one("SELECT count(*) FROM CurrentScan")
    if scanCount[0] == 0 :
        mylog('debug',[ '[insertOnlineHistory] - nothing to do, currentScan empty'])
        return 0

    History_All = db.read("SELECT * FROM Devices")
    History_All_Devices  = len(History_All)

    History_Archived = db.read("SELECT * FROM Devices WHERE dev_Archived = 1")
    History_Archived_Devices  = len(History_Archived)

    History_Online = db.read("SELECT * FROM CurrentScan")
    History_Online_Devices  = len(History_Online)
    History_Offline_Devices = History_All_Devices - History_Archived_Devices - History_Online_Devices

    sql.execute ("INSERT INTO Online_History (Scan_Date, Online_Devices, Down_Devices, All_Devices, Archived_Devices) "+
                 "VALUES ( ?, ?, ?, ?, ?)", (startTime, History_Online_Devices, History_Offline_Devices, History_All_Devices, History_Archived_Devices ) )
    db.commitDB()