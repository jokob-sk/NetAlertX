#!/usr/bin/env python

import os
import sys
import sqlite3

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from const import logPath, fullDbPath  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value("TIMEZONE"))

# Make sure log level is initialized correctly
Logger(get_setting_value("LOG_LEVEL"))

pluginName = "DBCLNP"

LOG_PATH = logPath + "/plugins"
LOG_FILE = os.path.join(LOG_PATH, f"script.{pluginName}.log")
RESULT_FILE = os.path.join(LOG_PATH, f"last_result.{pluginName}.log")


def main():

    PLUGINS_KEEP_HIST = int(get_setting_value("PLUGINS_KEEP_HIST"))
    HRS_TO_KEEP_NEWDEV = int(get_setting_value("HRS_TO_KEEP_NEWDEV"))
    HRS_TO_KEEP_OFFDEV = int(get_setting_value("HRS_TO_KEEP_OFFDEV"))
    DAYS_TO_KEEP_EVENTS = int(get_setting_value("DAYS_TO_KEEP_EVENTS"))
    CLEAR_NEW_FLAG = get_setting_value("CLEAR_NEW_FLAG")

    mylog("verbose", [f"[{pluginName}] In script"])

    # Execute cleanup/upkeep
    cleanup_database(
        fullDbPath,
        DAYS_TO_KEEP_EVENTS,
        HRS_TO_KEEP_NEWDEV,
        HRS_TO_KEEP_OFFDEV,
        PLUGINS_KEEP_HIST,
        CLEAR_NEW_FLAG,
    )

    mylog("verbose", [f"[{pluginName}] Cleanup complete"])

    return 0


# ===============================================================================
# Cleanup / upkeep database
# ===============================================================================
def cleanup_database(
    dbPath,
    DAYS_TO_KEEP_EVENTS,
    HRS_TO_KEEP_NEWDEV,
    HRS_TO_KEEP_OFFDEV,
    PLUGINS_KEEP_HIST,
    CLEAR_NEW_FLAG,
):
    """
    Cleaning out old records from the tables that don't need to keep all data.
    """

    mylog("verbose", [f"[{pluginName}] Upkeep Database:"])

    # Connect to the App database
    conn = sqlite3.connect(dbPath, timeout=30)
    cursor = conn.cursor()

    # -----------------------------------------------------
    # Cleanup Online History
    mylog(
        "verbose",
        [f"[{pluginName}] Online_History: Delete all but keep latest 150 entries"],
    )
    cursor.execute(
        """DELETE from Online_History where "Index" not in (
                            SELECT "Index" from Online_History
                            order by Scan_Date desc limit 150)"""
    )

    # -----------------------------------------------------
    # Cleanup Events
    mylog(
        "verbose",
        [
            f"[{pluginName}] Events: Delete all older than {str(DAYS_TO_KEEP_EVENTS)} days (DAYS_TO_KEEP_EVENTS setting)"
        ],
    )
    cursor.execute(
        f"""DELETE FROM Events
                            WHERE eve_DateTime <= date('now', '-{str(DAYS_TO_KEEP_EVENTS)} day')"""
    )
    # -----------------------------------------------------
    # Trim Plugins_History entries to less than PLUGINS_KEEP_HIST setting per unique "Plugin" column entry
    mylog(
        "verbose",
        [
            f"[{pluginName}] Plugins_History: Trim Plugins_History entries to less than {str(PLUGINS_KEEP_HIST)} per Plugin (PLUGINS_KEEP_HIST setting)"
        ],
    )

    # Build the SQL query to delete entries that exceed the limit per unique "Plugin" column entry
    delete_query = f"""DELETE FROM Plugins_History
                            WHERE "Index" NOT IN (
                                SELECT "Index"
                                FROM (
                                    SELECT "Index",
                                        ROW_NUMBER() OVER(PARTITION BY "Plugin" ORDER BY DateTimeChanged DESC) AS row_num
                                    FROM Plugins_History
                                ) AS ranked_objects
                                WHERE row_num <= {str(PLUGINS_KEEP_HIST)}
                            );"""

    cursor.execute(delete_query)

    # -----------------------------------------------------
    # Trim Notifications entries to less than DBCLNP_NOTIFI_HIST setting

    histCount = get_setting_value("DBCLNP_NOTIFI_HIST")

    mylog(
        "verbose",
        [
            f"[{pluginName}] Plugins_History: Trim Notifications entries to less than {histCount}"
        ],
    )

    # Build the SQL query to delete entries
    delete_query = f"""DELETE FROM Notifications
                            WHERE "Index" NOT IN (
                               SELECT "Index"
                                        FROM (
                                            SELECT "Index",
                                                ROW_NUMBER() OVER(PARTITION BY "Notifications" ORDER BY DateTimeCreated DESC) AS row_num
                                            FROM Notifications
                                        ) AS ranked_objects
                                        WHERE row_num <= {histCount}
                            );"""

    cursor.execute(delete_query)

    # -----------------------------------------------------
    # Trim Workflow entries to less than WORKFLOWS_AppEvents_hist setting
    histCount = get_setting_value("WORKFLOWS_AppEvents_hist")

    mylog("verbose", [f"[{pluginName}] Trim AppEvents to less than {histCount}"])

    # Build the SQL query to delete entries
    delete_query = f"""DELETE FROM AppEvents
                            WHERE "Index" NOT IN (
                               SELECT "Index"
                                        FROM (
                                            SELECT "Index",
                                                ROW_NUMBER() OVER(PARTITION BY "AppEvents" ORDER BY DateTimeCreated DESC) AS row_num
                                            FROM AppEvents
                                        ) AS ranked_objects
                                        WHERE row_num <= {histCount}
                            );"""

    cursor.execute(delete_query)
    conn.commit()

    # -----------------------------------------------------
    # Cleanup New Devices
    if HRS_TO_KEEP_NEWDEV != 0:
        mylog(
            "verbose",
            [
                f"[{pluginName}] Devices: Delete all New Devices older than {str(HRS_TO_KEEP_NEWDEV)} hours (HRS_TO_KEEP_NEWDEV setting)"
            ],
        )
        query = f"""DELETE FROM Devices WHERE devIsNew = 1 AND devFirstConnection < date('now', '-{str(HRS_TO_KEEP_NEWDEV)} hour')"""
        mylog("verbose", [f"[{pluginName}] Query: {query} "])
        cursor.execute(query)

    # -----------------------------------------------------
    # Cleanup Offline Devices
    if HRS_TO_KEEP_OFFDEV != 0:
        mylog(
            "verbose",
            [
                f"[{pluginName}] Devices: Delete all New Devices older than {str(HRS_TO_KEEP_OFFDEV)} hours (HRS_TO_KEEP_OFFDEV setting)"
            ],
        )
        query = f"""DELETE FROM Devices WHERE devPresentLastScan = 0 AND devLastConnection < date('now', '-{str(HRS_TO_KEEP_OFFDEV)} hour')"""
        mylog("verbose", [f"[{pluginName}] Query: {query} "])
        cursor.execute(query)

    # -----------------------------------------------------
    # Clear New Flag
    if CLEAR_NEW_FLAG != 0:
        mylog(
            "verbose",
            [
                f'[{pluginName}] Devices: Clear "New Device" flag for all devices older than {str(CLEAR_NEW_FLAG)} hours (CLEAR_NEW_FLAG setting)'
            ],
        )
        query = f"""UPDATE Devices SET devIsNew = 0 WHERE devIsNew = 1 AND date(devFirstConnection, '+{str(CLEAR_NEW_FLAG)} hour') < date('now')"""
        #  select * from Devices where devIsNew = 1 AND date(devFirstConnection, '+3 hour' ) < date('now')
        mylog("verbose", [f"[{pluginName}] Query: {query} "])
        cursor.execute(query)

    # -----------------------------------------------------
    # De-dupe (de-duplicate) from the Plugins_Objects table
    # TODO This shouldn't be necessary - probably a concurrency bug somewhere in the code :(
    mylog("verbose", [f"[{pluginName}] Plugins_Objects: Delete all duplicates"])
    cursor.execute(
        """
        DELETE FROM Plugins_Objects
        WHERE rowid > (
            SELECT MIN(rowid) FROM Plugins_Objects p2
            WHERE Plugins_Objects.Plugin = p2.Plugin
            AND Plugins_Objects.Object_PrimaryID = p2.Object_PrimaryID
            AND Plugins_Objects.Object_SecondaryID = p2.Object_SecondaryID
            AND Plugins_Objects.UserData = p2.UserData
        )
    """
    )

    conn.commit()

    # Check WAL file size
    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    cursor.execute("PRAGMA wal_checkpoint(FULL);")

    mylog("verbose", [f"[{pluginName}] WAL checkpoint executed to truncate file."])

    # Shrink DB
    mylog("verbose", [f"[{pluginName}] Shrink Database"])
    cursor.execute("VACUUM;")

    # Close the database connection
    conn.close()


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == "__main__":
    main()
