#!/bin/sh
# This script checks if the database file exists, and if not, creates it with the initial schema.
# It is intended to be run at the first start of the application.

# If ALWAYS_FRESH_INSTALL is true, remove the database to force a rebuild.
if [ "${ALWAYS_FRESH_INSTALL}" = "true" ]; then
    if [ -f "${NETALERTX_DB_FILE}" ]; then
        # Provide feedback to the user.
        >&2 echo "INFO: ALWAYS_FRESH_INSTALL is true. Removing existing database to force a fresh installation."
        rm -f "${NETALERTX_DB_FILE}" "${NETALERTX_DB_FILE}-shm" "${NETALERTX_DB_FILE}-wal"
    fi
# Otherwise, if the db exists, exit.
elif [ -f "${NETALERTX_DB_FILE}" ]; then
    exit 0
fi

CYAN=$(printf '\033[1;36m')
RESET=$(printf '\033[0m')
>&2 printf "%s" "${CYAN}"
>&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
🆕  First run detected. Building initial database schema in ${NETALERTX_DB_FILE}.

    Do not interrupt this step. Once complete, consider backing up the fresh
    database before onboarding sensitive networks.
══════════════════════════════════════════════════════════════════════════════
EOF
>&2 printf "%s" "${RESET}"

# Write all text to db file until we see "end-of-database-schema"
sqlite3 "${NETALERTX_DB_FILE}" <<'end-of-database-schema'
CREATE TABLE Events (eve_MAC STRING (50) NOT NULL COLLATE NOCASE, eve_IP STRING (50) NOT NULL COLLATE NOCASE, eve_DateTime DATETIME NOT NULL, eve_EventType STRING (30) NOT NULL COLLATE NOCASE, eve_AdditionalInfo STRING (250) DEFAULT (''), eve_PendingAlertEmail BOOLEAN NOT NULL CHECK (eve_PendingAlertEmail IN (0, 1)) DEFAULT (1), eve_PairEventRowid INTEGER);
CREATE TABLE Sessions (ses_MAC STRING (50) COLLATE NOCASE, ses_IP STRING (50) COLLATE NOCASE, ses_EventTypeConnection STRING (30) COLLATE NOCASE, ses_DateTimeConnection DATETIME, ses_EventTypeDisconnection STRING (30) COLLATE NOCASE, ses_DateTimeDisconnection DATETIME, ses_StillConnected BOOLEAN, ses_AdditionalInfo STRING (250));
CREATE TABLE IF NOT EXISTS "Online_History" (
            "Index"     INTEGER,
            "Scan_Date" TEXT,
            "Online_Devices"    INTEGER,
            "Down_Devices"      INTEGER,
            "All_Devices"       INTEGER,
            "Archived_Devices" INTEGER,
            "Offline_Devices" INTEGER,
            PRIMARY KEY("Index" AUTOINCREMENT)
          );
CREATE TABLE Devices (
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
          , "devCustomProps" TEXT);
CREATE TABLE IF NOT EXISTS "Settings" (
            "setKey"            TEXT,
            "setName"           TEXT,
            "setDescription"    TEXT,
            "setType"         TEXT,
            "setOptions"      TEXT,
            "setGroup"            TEXT,
            "setValue"        TEXT,
            "setEvents"         TEXT,
            "setOverriddenByEnv" INTEGER
            );
CREATE TABLE IF NOT EXISTS "Parameters" (
            "par_ID" TEXT PRIMARY KEY,
            "par_Value" TEXT
          );
CREATE TABLE Plugins_Objects(
                                    "Index"               INTEGER,
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
                        );
CREATE TABLE Plugins_Events(
                                    "Index"               INTEGER,
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
                                    "HelpVal4" TEXT, "ObjectGUID" TEXT,
                                    PRIMARY KEY("Index" AUTOINCREMENT)
                        );
CREATE TABLE Plugins_History(
                                    "Index"               INTEGER,
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
                                    "HelpVal4" TEXT, "ObjectGUID" TEXT,
                                    PRIMARY KEY("Index" AUTOINCREMENT)
                        );
CREATE TABLE Plugins_Language_Strings(
                                "Index"           INTEGER,
                                Language_Code TEXT NOT NULL,
                                String_Key TEXT NOT NULL,
                                String_Value TEXT NOT NULL,
                                Extra TEXT NOT NULL,
                                PRIMARY KEY("Index" AUTOINCREMENT)
                        );
CREATE TABLE CurrentScan (                                
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
CREATE TABLE IF NOT EXISTS "AppEvents" (
                "Index" INTEGER PRIMARY KEY AUTOINCREMENT,
                "GUID" TEXT UNIQUE,
                "AppEventProcessed" BOOLEAN,
                "DateTimeCreated" TEXT,
                "ObjectType" TEXT,
                "ObjectGUID" TEXT,
                "ObjectPlugin" TEXT,
                "ObjectPrimaryID" TEXT,
                "ObjectSecondaryID" TEXT,
                "ObjectForeignKey" TEXT,
                "ObjectIndex" TEXT,            
                "ObjectIsNew" BOOLEAN, 
                "ObjectIsArchived" BOOLEAN, 
                "ObjectStatusColumn" TEXT,
                "ObjectStatus" TEXT,            
                "AppEventType" TEXT,
                "Helper1" TEXT,
                "Helper2" TEXT,
                "Helper3" TEXT,
                "Extra" TEXT
            );
CREATE TABLE IF NOT EXISTS "Notifications" (
            "Index"           INTEGER,
            "GUID"            TEXT UNIQUE,
            "DateTimeCreated" TEXT,
            "DateTimePushed"  TEXT,
            "Status"          TEXT,
            "JSON"            TEXT,
            "Text"            TEXT,
            "HTML"            TEXT,
            "PublishedVia"    TEXT,
            "Extra"           TEXT,
            PRIMARY KEY("Index" AUTOINCREMENT)
        );
CREATE INDEX IDX_eve_DateTime ON Events (eve_DateTime);
CREATE INDEX IDX_eve_EventType ON Events (eve_EventType COLLATE NOCASE);
CREATE INDEX IDX_eve_MAC ON Events (eve_MAC COLLATE NOCASE);
CREATE INDEX IDX_eve_PairEventRowid ON Events (eve_PairEventRowid);
CREATE INDEX IDX_ses_EventTypeDisconnection ON Sessions (ses_EventTypeDisconnection COLLATE NOCASE);
CREATE INDEX IDX_ses_EventTypeConnection ON Sessions (ses_EventTypeConnection COLLATE NOCASE);
CREATE INDEX IDX_ses_DateTimeDisconnection ON Sessions (ses_DateTimeDisconnection);
CREATE INDEX IDX_ses_MAC ON Sessions (ses_MAC COLLATE NOCASE);
CREATE INDEX IDX_ses_DateTimeConnection ON Sessions (ses_DateTimeConnection);
CREATE INDEX IDX_dev_PresentLastScan ON Devices (devPresentLastScan);
CREATE INDEX IDX_dev_FirstConnection ON Devices (devFirstConnection);
CREATE INDEX IDX_dev_AlertDeviceDown ON Devices (devAlertDown);
CREATE INDEX IDX_dev_StaticIP ON Devices (devStaticIP);
CREATE INDEX IDX_dev_ScanCycle ON Devices (devScan);
CREATE INDEX IDX_dev_Favorite ON Devices (devFavorite);
CREATE INDEX IDX_dev_LastIP ON Devices (devLastIP);
CREATE INDEX IDX_dev_NewDevice ON Devices (devIsNew);
CREATE INDEX IDX_dev_Archived ON Devices (devIsArchived);
CREATE VIEW Events_Devices AS 
                            SELECT * 
                            FROM Events 
                            LEFT JOIN Devices ON eve_MAC = devMac
/* Events_Devices(eve_MAC,eve_IP,eve_DateTime,eve_EventType,eve_AdditionalInfo,eve_PendingAlertEmail,eve_PairEventRowid,devMac,devName,devOwner,devType,devVendor,devFavorite,devGroup,devComments,devFirstConnection,devLastConnection,devLastIP,devStaticIP,devScan,devLogEvents,devAlertEvents,devAlertDown,devSkipRepeated,devLastNotification,devPresentLastScan,devIsNew,devLocation,devIsArchived,devParentMAC,devParentPort,devIcon,devGUID,devSite,devSSID,devSyncHubNode,devSourcePlugin,devCustomProps) */;
CREATE VIEW LatestEventsPerMAC AS
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
                                WHERE e.row_num = 1
/* LatestEventsPerMAC(eve_MAC,eve_IP,eve_DateTime,eve_EventType,eve_AdditionalInfo,eve_PendingAlertEmail,eve_PairEventRowid,row_num,devMac,devName,devOwner,devType,devVendor,devFavorite,devGroup,devComments,devFirstConnection,devLastConnection,devLastIP,devStaticIP,devScan,devLogEvents,devAlertEvents,devAlertDown,devSkipRepeated,devLastNotification,devPresentLastScan,devIsNew,devLocation,devIsArchived,devParentMAC,devParentPort,devIcon,devGUID,devSite,devSSID,devSyncHubNode,devSourcePlugin,devCustomProps,cur_MAC,cur_IP,cur_Vendor,cur_ScanMethod,cur_Name,cur_LastQuery,cur_DateTime,cur_SyncHubNodeName,cur_NetworkSite,cur_SSID,cur_NetworkNodeMAC,cur_PORT,cur_Type) */;
CREATE VIEW Sessions_Devices AS SELECT * FROM Sessions LEFT JOIN "Devices" ON ses_MAC = devMac
/* Sessions_Devices(ses_MAC,ses_IP,ses_EventTypeConnection,ses_DateTimeConnection,ses_EventTypeDisconnection,ses_DateTimeDisconnection,ses_StillConnected,ses_AdditionalInfo,devMac,devName,devOwner,devType,devVendor,devFavorite,devGroup,devComments,devFirstConnection,devLastConnection,devLastIP,devStaticIP,devScan,devLogEvents,devAlertEvents,devAlertDown,devSkipRepeated,devLastNotification,devPresentLastScan,devIsNew,devLocation,devIsArchived,devParentMAC,devParentPort,devIcon,devGUID,devSite,devSSID,devSyncHubNode,devSourcePlugin,devCustomProps) */;
CREATE VIEW Convert_Events_to_Sessions AS  SELECT EVE1.eve_MAC,
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
                                      EVE1.eve_PairEventRowID IS NULL
/* Convert_Events_to_Sessions(eve_MAC,eve_IP,eve_EventTypeConnection,eve_DateTimeConnection,eve_EventTypeDisconnection,eve_DateTimeDisconnection,eve_StillConnected,eve_AdditionalInfo) */;
CREATE TRIGGER "trg_insert_devices"
            AFTER INSERT ON "Devices"
            WHEN NOT EXISTS (
                SELECT 1 FROM AppEvents 
                WHERE AppEventProcessed = 0 
                AND ObjectType = 'Devices'
                AND ObjectGUID = NEW.devGUID
                AND ObjectStatus = CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END 
                AND AppEventType = 'insert'
            )
            BEGIN
                INSERT INTO "AppEvents" (
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
                    "ObjectPlugin",
                    "AppEventType"
                )
                VALUES (
                    
                lower(
                    hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' || 
                    substr(hex( randomblob(2)), 2) || '-' || 
                    substr('AB89', 1 + (abs(random()) % 4) , 1)  ||
                    substr(hex(randomblob(2)), 2) || '-' || 
                    hex(randomblob(6))
                )
            , 
                    DATETIME('now'), 
                    FALSE, 
                    'Devices', 
                    NEW.devGUID,  -- ObjectGUID
                    NEW.devMac,  -- ObjectPrimaryID
                    NEW.devLastIP,  -- ObjectSecondaryID
                    CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END,  -- ObjectStatus
                    'devPresentLastScan',  -- ObjectStatusColumn
                    NEW.devIsNew,  -- ObjectIsNew
                    NEW.devIsArchived,  -- ObjectIsArchived
                    NEW.devGUID,  -- ObjectForeignKey
                    'DEVICES',  -- ObjectForeignKey
                    'insert'
                );
            END;
CREATE TRIGGER "trg_update_devices"
            AFTER UPDATE ON "Devices"
            WHEN NOT EXISTS (
                SELECT 1 FROM AppEvents 
                WHERE AppEventProcessed = 0 
                AND ObjectType = 'Devices'
                AND ObjectGUID = NEW.devGUID
                AND ObjectStatus = CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END 
                AND AppEventType = 'update'
            )
            BEGIN
                INSERT INTO "AppEvents" (
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
                    "ObjectPlugin",
                    "AppEventType"
                )
                VALUES (
                    
                lower(
                    hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' || 
                    substr(hex( randomblob(2)), 2) || '-' || 
                    substr('AB89', 1 + (abs(random()) % 4) , 1)  ||
                    substr(hex(randomblob(2)), 2) || '-' || 
                    hex(randomblob(6))
                )
            , 
                    DATETIME('now'), 
                    FALSE, 
                    'Devices', 
                    NEW.devGUID,  -- ObjectGUID
                    NEW.devMac,  -- ObjectPrimaryID
                    NEW.devLastIP,  -- ObjectSecondaryID
                    CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END,  -- ObjectStatus
                    'devPresentLastScan',  -- ObjectStatusColumn
                    NEW.devIsNew,  -- ObjectIsNew
                    NEW.devIsArchived,  -- ObjectIsArchived
                    NEW.devGUID,  -- ObjectForeignKey
                    'DEVICES',  -- ObjectForeignKey
                    'update'
                );
            END;
CREATE TRIGGER "trg_delete_devices"
            AFTER DELETE ON "Devices"
            WHEN NOT EXISTS (
                SELECT 1 FROM AppEvents 
                WHERE AppEventProcessed = 0 
                AND ObjectType = 'Devices'
                AND ObjectGUID = OLD.devGUID
                AND ObjectStatus = CASE WHEN OLD.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END 
                AND AppEventType = 'delete'
            )
            BEGIN
                INSERT INTO "AppEvents" (
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
                    "ObjectPlugin",
                    "AppEventType"
                )
                VALUES (
                    
                lower(
                    hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' || 
                    substr(hex( randomblob(2)), 2) || '-' || 
                    substr('AB89', 1 + (abs(random()) % 4) , 1)  ||
                    substr(hex(randomblob(2)), 2) || '-' || 
                    hex(randomblob(6))
                )
            , 
                    DATETIME('now'), 
                    FALSE, 
                    'Devices', 
                    OLD.devGUID,  -- ObjectGUID
                    OLD.devMac,  -- ObjectPrimaryID
                    OLD.devLastIP,  -- ObjectSecondaryID
                    CASE WHEN OLD.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END,  -- ObjectStatus
                    'devPresentLastScan',  -- ObjectStatusColumn
                    OLD.devIsNew,  -- ObjectIsNew
                    OLD.devIsArchived,  -- ObjectIsArchived
                    OLD.devGUID,  -- ObjectForeignKey
                    'DEVICES',  -- ObjectForeignKey
                    'delete'
                );
            END;
end-of-database-schema

if [ $? -ne 0 ]; then
  RED=$(printf '\033[1;31m')
  RESET=$(printf '\033[0m')
  >&2 printf "%s" "${RED}"
  >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
❌  CRITICAL: Database schema creation failed for ${NETALERTX_DB_FILE}.

    NetAlertX cannot start without a properly initialized database. This
    failure typically indicates:

    * Insufficient disk space or write permissions in the database directory
    * Corrupted or inaccessible SQLite installation
    * File system issues preventing database file creation

    Check the logs for detailed SQLite error messages. Ensure the container
    has write access to the database path and adequate storage space.
══════════════════════════════════════════════════════════════════════════════
EOF
  >&2 printf "%s" "${RESET}"
  exit 1
fi