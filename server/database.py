""" all things database to support NetAlertX """

import sqlite3
import base64
import json

# Register NetAlertX modules 
from const import fullDbPath, sql_devices_stats, sql_devices_all, sql_generateGuid

from logger import mylog
from helper import json_obj, initOrSetParam, row_to_json, timeNowTZ
from workflows.app_events import AppEvent_obj
from db.db_upgrade import ensure_column, ensure_views, ensure_CurrentScan, ensure_plugins_tables, ensure_Parameters, ensure_Settings, ensure_Indexes

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
    def initDB(self):
        """
        Check the current tables in the DB and upgrade them if neccessary
        """

        # Add Devices fields if missing
            
        # devFQDN 
        if ensure_column(self.sql, "Devices", "devFQDN", "TEXT") is False:
            return # addition failed

        # devParentRelType 
        if ensure_column(self.sql, "Devices", "devParentRelType", "TEXT") is False:
            return # addition failed

        # devRequireNicsOnline 
        if ensure_column(self.sql, "Devices", "devReqNicsOnline", "INTEGER") is False:
            return # addition failed
        
        # Settings table setup
        ensure_Settings(self.sql)

        # Parameters tables setup
        ensure_Parameters(self.sql)
        
        # Plugins tables setup
        ensure_plugins_tables(self.sql)
       
        # CurrentScan table setup
        ensure_CurrentScan(self.sql)
        
        # Views        
        ensure_views(self.sql)

        # Views        
        ensure_Indexes(self.sql)

        # commit changes
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

