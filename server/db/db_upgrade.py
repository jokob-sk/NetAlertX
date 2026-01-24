import sys
import os

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog  # noqa: E402 [flake8 lint suppression]
from messaging.in_app import write_notification  # noqa: E402 [flake8 lint suppression]


# Define the expected Devices table columns (hardcoded base schema) [v26.1/2.XX]
EXPECTED_DEVICES_COLUMNS = [
    "devMac",
    "devName",
    "devOwner",
    "devType",
    "devVendor",
    "devFavorite",
    "devGroup",
    "devComments",
    "devFirstConnection",
    "devLastConnection",
    "devLastIP",
    "devFQDN",
    "devPrimaryIPv4",
    "devPrimaryIPv6",
    "devVlan",
    "devForceStatus",
    "devStaticIP",
    "devScan",
    "devLogEvents",
    "devAlertEvents",
    "devAlertDown",
    "devSkipRepeated",
    "devLastNotification",
    "devPresentLastScan",
    "devIsNew",
    "devLocation",
    "devIsArchived",
    "devParentMAC",
    "devParentPort",
    "devParentRelType",
    "devReqNicsOnline",
    "devIcon",
    "devGUID",
    "devSite",
    "devSSID",
    "devSyncHubNode",
    "devSourcePlugin",
    "devMacSource",
    "devNameSource",
    "devFqdnSource",
    "devLastIpSource",
    "devVendorSource",
    "devSsidSource",
    "devParentMacSource",
    "devParentPortSource",
    "devParentRelTypeSource",
    "devVlanSource",
    "devCustomProps",
]


def ensure_column(sql, table: str, column_name: str, column_type: str) -> bool:
    """
    Ensures a column exists in the specified table. If missing, attempts to add it.
    Returns True on success, False on failure.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute() and fetchall()).
    - table: name of the table (e.g., "Devices").
    - column_name: name of the column to ensure.
    - column_type: SQL type of the column (e.g., "TEXT", "INTEGER", "BOOLEAN").
    """

    try:
        # Get actual columns from DB
        sql.execute(f'PRAGMA table_info("{table}")')
        actual_columns = [row[1] for row in sql.fetchall()]

        # Check if target column is already present
        if column_name in actual_columns:
            return True  # Already exists

        # Validate that this column is in the expected schema
        expected = EXPECTED_DEVICES_COLUMNS if table == "Devices" else []
        if not expected or column_name not in expected:
            msg = (
                f"[db_upgrade] ⚠ ERROR: Column '{column_name}' is not in expected schema - "
                f"aborting to prevent corruption. "
                "Check https://docs.netalertx.com/UPDATES"
            )
            mylog("none", [msg])
            write_notification(msg)
            return False

        # Add missing column
        mylog("verbose", [f"[db_upgrade] Adding '{column_name}' ({column_type}) to {table} table"],)
        sql.execute(f'ALTER TABLE "{table}" ADD "{column_name}" {column_type}')
        return True

    except Exception as e:
        mylog("none", [f"[db_upgrade] ERROR while adding '{column_name}': {e}"])
        return False


def ensure_views(sql) -> bool:
    """
    Ensures required views exist.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute() and fetchall()).
    """
    sql.execute(""" DROP VIEW IF EXISTS Events_Devices;""")
    sql.execute(""" CREATE VIEW Events_Devices AS
                            SELECT *
                            FROM Events
                            LEFT JOIN Devices ON eve_MAC = devMac;
                          """)

    sql.execute(""" DROP VIEW IF EXISTS LatestEventsPerMAC;""")
    sql.execute("""CREATE VIEW LatestEventsPerMAC AS
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

    sql.execute(""" DROP VIEW IF EXISTS Sessions_Devices;""")
    sql.execute(
        """CREATE VIEW Sessions_Devices AS SELECT * FROM Sessions LEFT JOIN "Devices" ON ses_MAC = devMac;"""
    )

    # handling the Convert_Events_to_Sessions / Sessions screens
    sql.execute("""DROP VIEW IF EXISTS Convert_Events_to_Sessions;""")
    sql.execute("""CREATE VIEW Convert_Events_to_Sessions AS  SELECT EVE1.eve_MAC,
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

    sql.execute(""" DROP VIEW IF EXISTS LatestDeviceScan;""")
    sql.execute(""" CREATE VIEW LatestDeviceScan AS
                        WITH RankedScans AS (
                            SELECT
                                c.*,
                                ROW_NUMBER() OVER (
                                    PARTITION BY c.cur_MAC, c.cur_ScanMethod
                                    ORDER BY c.cur_DateTime DESC
                                ) AS rn
                            FROM CurrentScan c
                        )
                        SELECT
                            d.*,           -- all Device fields
                            r.*            -- all CurrentScan fields (cur_*)
                        FROM Devices d
                        LEFT JOIN RankedScans r
                            ON d.devMac = r.cur_MAC
                        WHERE r.rn = 1;

                          """)

    return True


def ensure_Indexes(sql) -> bool:
    """
    Ensures required indexes exist with correct structure.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute()).
    """
    indexes = [
        # Sessions
        (
            "idx_ses_mac_date",
            "CREATE INDEX idx_ses_mac_date ON Sessions(ses_MAC, ses_DateTimeConnection, ses_DateTimeDisconnection, ses_StillConnected)",
        ),
        # Events
        (
            "idx_eve_mac_date_type",
            "CREATE INDEX idx_eve_mac_date_type ON Events(eve_MAC, eve_DateTime, eve_EventType)",
        ),
        (
            "idx_eve_alert_pending",
            "CREATE INDEX idx_eve_alert_pending ON Events(eve_PendingAlertEmail)",
        ),
        (
            "idx_eve_mac_datetime_desc",
            "CREATE INDEX idx_eve_mac_datetime_desc ON Events(eve_MAC, eve_DateTime DESC)",
        ),
        (
            "idx_eve_pairevent",
            "CREATE INDEX idx_eve_pairevent ON Events(eve_PairEventRowID)",
        ),
        (
            "idx_eve_type_date",
            "CREATE INDEX idx_eve_type_date ON Events(eve_EventType, eve_DateTime)",
        ),
        # Devices
        ("idx_dev_mac", "CREATE INDEX idx_dev_mac ON Devices(devMac)"),
        (
            "idx_dev_present",
            "CREATE INDEX idx_dev_present ON Devices(devPresentLastScan)",
        ),
        (
            "idx_dev_alertdown",
            "CREATE INDEX idx_dev_alertdown ON Devices(devAlertDown)",
        ),
        ("idx_dev_isnew", "CREATE INDEX idx_dev_isnew ON Devices(devIsNew)"),
        (
            "idx_dev_isarchived",
            "CREATE INDEX idx_dev_isarchived ON Devices(devIsArchived)",
        ),
        ("idx_dev_favorite", "CREATE INDEX idx_dev_favorite ON Devices(devFavorite)"),
        (
            "idx_dev_parentmac",
            "CREATE INDEX idx_dev_parentmac ON Devices(devParentMAC)",
        ),
        # Optional filter indexes
        ("idx_dev_site", "CREATE INDEX idx_dev_site ON Devices(devSite)"),
        ("idx_dev_group", "CREATE INDEX idx_dev_group ON Devices(devGroup)"),
        ("idx_dev_owner", "CREATE INDEX idx_dev_owner ON Devices(devOwner)"),
        ("idx_dev_type", "CREATE INDEX idx_dev_type ON Devices(devType)"),
        ("idx_dev_vendor", "CREATE INDEX idx_dev_vendor ON Devices(devVendor)"),
        ("idx_dev_location", "CREATE INDEX idx_dev_location ON Devices(devLocation)"),
        # Settings
        ("idx_set_key", "CREATE INDEX idx_set_key ON Settings(setKey)"),
        # Plugins_Objects
        (
            "idx_plugins_plugin_mac_ip",
            "CREATE INDEX idx_plugins_plugin_mac_ip ON Plugins_Objects(Plugin, Object_PrimaryID, Object_SecondaryID)",
        ),  # Issue #1251: Optimize name resolution lookup
    ]

    for name, create_sql in indexes:
        sql.execute(f"DROP INDEX IF EXISTS {name};")
        sql.execute(create_sql + ";")

    return True


def ensure_CurrentScan(sql) -> bool:
    """
    Ensures required CurrentScan table exist.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute() and fetchall()).
    """
    # 🐛 CurrentScan DEBUG: comment out below when debugging to keep the CurrentScan table after restarts/scan finishes
    sql.execute("DROP TABLE IF EXISTS CurrentScan;")
    sql.execute(""" CREATE TABLE IF NOT EXISTS CurrentScan (
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
                                cur_devVlan STRING(250),
                                cur_NetworkNodeMAC STRING(250),
                                cur_PORT STRING(250),
                                cur_Type STRING(250)
                            );
                        """)

    return True


def ensure_Parameters(sql) -> bool:
    """
    Ensures required Parameters table exist.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute() and fetchall()).
    """

    # Re-creating Parameters table
    mylog("verbose", ["[db_upgrade] Re-creating Parameters table"])
    sql.execute("DROP TABLE Parameters;")

    sql.execute("""
          CREATE TABLE "Parameters" (
            "par_ID" TEXT PRIMARY KEY,
            "par_Value"	TEXT
          );
          """)

    return True


def ensure_Settings(sql) -> bool:
    """
    Ensures required Settings table exist.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute() and fetchall()).
    """

    # Re-creating Settings table
    mylog("verbose", ["[db_upgrade] Re-creating Settings table"])

    sql.execute(""" DROP TABLE IF EXISTS Settings;""")
    sql.execute("""
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

    return True


def ensure_plugins_tables(sql) -> bool:
    """
    Ensures required plugins tables exist.

    Parameters:
    - sql: database cursor or connection wrapper (must support execute() and fetchall()).
    """

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
    sql.execute(sql_Plugins_Objects)

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
    sql.execute(sql_Plugins_Events)

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
    sql.execute(sql_Plugins_History)

    # Dynamically generated language strings
    sql.execute("DROP TABLE IF EXISTS Plugins_Language_Strings;")
    sql.execute(""" CREATE TABLE IF NOT EXISTS Plugins_Language_Strings(
                                "Index"	          INTEGER,
                                Language_Code TEXT NOT NULL,
                                String_Key TEXT NOT NULL,
                                String_Value TEXT NOT NULL,
                                Extra TEXT NOT NULL,
                                PRIMARY KEY("Index" AUTOINCREMENT)
                        ); """)

    return True
