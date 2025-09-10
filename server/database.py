""" all things database to support NetAlertX """

import sqlite3

# Register NetAlertX modules 
from const import fullDbPath, sql_devices_stats, sql_devices_all

from logger import mylog
from db.db_helper import get_table_json, json_obj
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
    def open(self):
        # Check if DB is open
        if self.sql_connection is not None:
            mylog('debug', 'openDB: database already open')
            return

        mylog('verbose', '[Database] Opening DB')
        # Open DB and Cursor
        try:
            self.sql_connection = sqlite3.connect(fullDbPath, isolation_level=None)

            # The WAL journaling mode uses a write-ahead log instead of a
            # rollback journal to implement transactions.
            self.sql_connection.execute('pragma journal_mode=WAL;')
            # When synchronous is NORMAL (1), the SQLite database engine will still sync
            # at the most critical moments, but less often than in FULL mode.
            self.sql_connection.execute('PRAGMA synchronous=NORMAL;')
            # When temp_store is MEMORY (2) temporary tables and indices
            # are kept as if they were in pure in-memory databases.
            self.sql_connection.execute('PRAGMA temp_store=MEMORY;')

            self.sql_connection.text_factory = str
            self.sql_connection.row_factory = sqlite3.Row
            self.sql = self.sql_connection.cursor()
        except sqlite3.Error as e:
            mylog('minimal', ['[Database] - Open DB Error: ', e])


    #-------------------------------------------------------------------------------
    def commitDB(self):
        if self.sql_connection is None:
            mylog('debug', 'commitDB: database is not open')
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
        if self.sql_connection is None:
            mylog('debug', 'getQueryArray: database is not open')
            return

        self.sql.execute(query)
        rows = self.sql.fetchall()
        # self.commitDB()

        # Convert result into list of lists
        # Efficiently convert each row to a list

        return [list(row) for row in rows]


    #-------------------------------------------------------------------------------
    def initDB(self):
        """
        Check the current tables in the DB and upgrade them if neccessary
        """

        # Add Devices fields if missing

        # devFQDN
        if ensure_column(self.sql, "Devices", "devFQDN", "TEXT") is False:
            return  # addition failed

        # devParentRelType 
        if ensure_column(self.sql, "Devices", "devParentRelType", "TEXT") is False:
            return  # addition failed

        # devRequireNicsOnline 
        if ensure_column(self.sql, "Devices", "devReqNicsOnline", "INTEGER") is False:
            return  # addition failed

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


    # #-------------------------------------------------------------------------------
    # def get_table_as_json(self, sqlQuery):

    #     # mylog('debug',[ '[Database] - get_table_as_json - Query: ', sqlQuery])
    #     try:
    #         self.sql.execute(sqlQuery)
    #         columnNames = list(map(lambda x: x[0], self.sql.description))
    #         rows = self.sql.fetchall()
    #     except sqlite3.Error as e:
    #         mylog('verbose',[ '[Database] - SQL ERROR: ', e])
    #         return json_obj({}, []) # return empty object

    #     result = {"data":[]}
    #     for row in rows:
    #         tmp = row_to_json(columnNames, row)
    #         result["data"].append(tmp)

    #     # mylog('debug',[ '[Database] - get_table_as_json - returning ', len(rows), " rows with columns: ", columnNames])
    #     # mylog('debug',[ '[Database] - get_table_as_json - returning json ', json.dumps(result) ])
    #     return json_obj(result, columnNames)

    def get_table_as_json(self, sqlQuery):
        """
        Wrapper to use the central get_table_as_json helper.
        """
        try:
            result = get_table_json(self.sql, sqlQuery)
        except Exception as e:
            mylog('minimal', ['[Database] - get_table_as_json ERROR:', e])
            return json_obj({}, [])  # return empty object on failure

        # mylog('debug',[ '[Database] - get_table_as_json - returning ', len(rows), " rows with columns: ", columnNames])
        # mylog('debug',[ '[Database] - get_table_as_json - returning json ', json.dumps(result) ])

        return result

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
            mylog('minimal', [ '[Database] - ERROR: inconsistent query and/or arguments.', query, " params: ", args])
        except sqlite3.Error as e:
            mylog('minimal', [ '[Database] - SQL ERROR: ', e])
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

def get_temp_db_connection():
    """
    Returns a new SQLite connection with Row factory.
    Should be used per-thread/request to avoid cross-thread issues.
    """
    conn = sqlite3.connect(fullDbPath, timeout=5, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")  # 5s wait before giving up
    conn.row_factory = sqlite3.Row
    return conn
