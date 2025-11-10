import os
import sys

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from helper import get_setting_value
from logger import Logger
from const import sql_generateGuid

# Make sure log level is initialized correctly
Logger(get_setting_value("LOG_LEVEL"))


class AppEvent_obj:
    def __init__(self, db):
        self.db = db

        # Drop existing table
        self.db.sql.execute("""DROP TABLE IF EXISTS "AppEvents" """)

        # Drop all triggers
        self.drop_all_triggers()

        # Create the AppEvents table if missing
        self.create_app_events_table()

        # Define object mapping for different table structures, including fields, expressions, and constants
        self.object_mapping = {
            "Devices": {
                "fields": {
                    "ObjectGUID": "NEW.devGUID",
                    "ObjectPrimaryID": "NEW.devMac",
                    "ObjectSecondaryID": "NEW.devLastIP",
                    "ObjectForeignKey": "NEW.devGUID",
                    "ObjectStatus": "CASE WHEN NEW.devPresentLastScan = 1 THEN 'online' ELSE 'offline' END",
                    "ObjectStatusColumn": "'devPresentLastScan'",
                    "ObjectIsNew": "NEW.devIsNew",
                    "ObjectIsArchived": "NEW.devIsArchived",
                    "ObjectPlugin": "'DEVICES'",
                }
            }
            # ,
            # "Plugins_Objects": {
            #     "fields": {
            #         "ObjectGUID": "NEW.ObjectGUID",
            #         "ObjectPrimaryID": "NEW.Plugin",
            #         "ObjectSecondaryID": "NEW.Object_PrimaryID",
            #         "ObjectForeignKey": "NEW.ForeignKey",
            #         "ObjectStatus": "NEW.Status",
            #         "ObjectStatusColumn": "'Status'",
            #         "ObjectIsNew": "CASE WHEN NEW.Status = 'new' THEN 1 ELSE 0 END",
            #         "ObjectIsArchived": "0",  # Default value
            #         "ObjectPlugin": "NEW.Plugin"
            #     }
            # }
        }

        # Re-Create triggers dynamically
        for table, config in self.object_mapping.items():
            self.create_trigger(table, "insert", config)
            self.create_trigger(table, "update", config)
            self.create_trigger(table, "delete", config)

        self.save()

    def drop_all_triggers(self):
        """Drops all relevant triggers to ensure a clean start."""
        self.db.sql.execute("""
            SELECT 'DROP TRIGGER IF EXISTS ' || name || ';'
            FROM sqlite_master
            WHERE type = 'trigger';
        """)

        # Fetch all drop statements
        drop_statements = self.db.sql.fetchall()

        # Execute each drop statement
        for statement in drop_statements:
            self.db.sql.execute(statement[0])

        self.save()

    def create_app_events_table(self):
        """Creates the AppEvents table if it doesn't exist."""
        self.db.sql.execute("""
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
        """)

    def create_trigger(self, table_name, event, config):
        """Generic function to create triggers dynamically."""
        trigger_name = f"trg_{event}_{table_name.lower()}"

        query = f"""
         CREATE TRIGGER IF NOT EXISTS "{trigger_name}"
            AFTER {event.upper()} ON "{table_name}"
            WHEN NOT EXISTS (
                SELECT 1 FROM AppEvents 
                WHERE AppEventProcessed = 0 
                AND ObjectType = '{table_name}'
                AND ObjectGUID = {manage_prefix(config["fields"]["ObjectGUID"], event)}
                AND ObjectStatus = {manage_prefix(config["fields"]["ObjectStatus"], event)} 
                AND AppEventType = '{event.lower()}'
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
                    {sql_generateGuid}, 
                    DATETIME('now'), 
                    FALSE, 
                    '{table_name}', 
                    {manage_prefix(config["fields"]["ObjectGUID"], event)},  -- ObjectGUID
                    {manage_prefix(config["fields"]["ObjectPrimaryID"], event)},  -- ObjectPrimaryID
                    {manage_prefix(config["fields"]["ObjectSecondaryID"], event)},  -- ObjectSecondaryID
                    {manage_prefix(config["fields"]["ObjectStatus"], event)},  -- ObjectStatus
                    {manage_prefix(config["fields"]["ObjectStatusColumn"], event)},  -- ObjectStatusColumn
                    {manage_prefix(config["fields"]["ObjectIsNew"], event)},  -- ObjectIsNew
                    {manage_prefix(config["fields"]["ObjectIsArchived"], event)},  -- ObjectIsArchived
                    {manage_prefix(config["fields"]["ObjectForeignKey"], event)},  -- ObjectForeignKey
                    {manage_prefix(config["fields"]["ObjectPlugin"], event)},  -- ObjectForeignKey
                    '{event.lower()}'
                );
            END;
        """

        # mylog("verbose", [query])

        self.db.sql.execute(query)

    def save(self):
        # Commit changes
        self.db.commitDB()


# Manage prefixes of column names
def manage_prefix(field, event):
    if event == "delete":
        return field.replace("NEW.", "OLD.")
    return field
