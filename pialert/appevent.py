import datetime
import json
import uuid

# PiAlert modules
import conf
import const
from const import pialertPath, logPath, apiPath
from logger import logResult, mylog, print_log
from helper import  timeNowTZ

#-------------------------------------------------------------------------------
# Execution object handling
#-------------------------------------------------------------------------------
class AppEvent_obj:
    def __init__(self, db):
        self.db = db

        # Create AppEvent table if missing
        self.db.sql.execute("""CREATE TABLE IF NOT EXISTS "AppEvents" (
            "Index"                 INTEGER,
            "GUID"                  TEXT UNIQUE,
            "DateTimeCreated"       TEXT,
            "ObjectType"            TEXT, -- ObjectType (Plugins, Notifications, Events)
            "ObjectGUID"            TEXT,
            "ObjectPlugin"          TEXT,
            "ObjectMAC"             TEXT,
            "ObjectIP"              TEXT,
            "ObjectPrimaryID"       TEXT,
            "ObjectSecondaryID"     TEXT,
            "ObjectForeignKey"      TEXT,
            "ObjectIndex"           TEXT,
            "ObjectRowID"           TEXT,
            "ObjectStatusColumn"    TEXT, -- Status (Notifications, Plugins), eve_EventType (Events)
            "ObjectStatus"          TEXT, -- new_devices, down_devices, events, new, watched-changed, watched-not-changed, missing-in-last-scan, Device down, New Device, IP Changed, Connected, Disconnected, VOIDED - Disconnected, VOIDED - Connected, <missing event>
            "AppEventStatus"        TEXT, -- TBD "new", "used", "cleanup-next"
            "Extra"                 TEXT,
            PRIMARY KEY("Index" AUTOINCREMENT)
        );
        """)

        self.save()

    # Create a new DB entry if new notifications are available, otherwise skip
    def create(self, Extra="", **kwargs):
        # Check if nothing to report, end
        if not any(kwargs.values()):
            return False

        # Continue and save into DB if notifications are available
        self.GUID = str(uuid.uuid4())
        self.DateTimeCreated = timeNowTZ()
        self.ObjectType = "Plugins"  # Modify ObjectType as needed

        # Optional parameters
        self.ObjectGUID         = kwargs.get("ObjectGUID", "")
        self.ObjectPlugin       = kwargs.get("ObjectPlugin", "")
        self.ObjectMAC          = kwargs.get("ObjectMAC", "")
        self.ObjectIP           = kwargs.get("ObjectIP", "")
        self.ObjectPrimaryID    = kwargs.get("ObjectPrimaryID", "")
        self.ObjectSecondaryID  = kwargs.get("ObjectSecondaryID", "")
        self.ObjectForeignKey   = kwargs.get("ObjectForeignKey", "")
        self.ObjectIndex        = kwargs.get("ObjectIndex", "")
        self.ObjectRowID        = kwargs.get("ObjectRowID", "")
        self.ObjectStatusColumn = kwargs.get("ObjectStatusColumn", "")
        self.ObjectStatus       = kwargs.get("ObjectStatus", "")

        self.AppEventStatus = "new"  # Modify AppEventStatus as needed
        self.Extra = Extra

        self.upsert()

        return True

    # Update the status of the entry
    def updateStatus(self, newStatus):
        self.ObjectStatus = newStatus
        self.upsert()

    def upsert(self):
        self.db.sql.execute("""
            INSERT OR REPLACE INTO AppEvents (
                "GUID", 
                "DateTimeCreated", 
                "ObjectType", 
                "ObjectGUID", 
                "ObjectPlugin", 
                "ObjectMAC", 
                "ObjectIP", 
                "ObjectPrimaryID", 
                "ObjectSecondaryID", 
                "ObjectForeignKey", 
                "ObjectIndex", 
                "ObjectRowID", 
                "ObjectStatusColumn", 
                "ObjectStatus", 
                "AppEventStatus", 
                "Extra"
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.GUID, 
            self.DateTimeCreated, 
            self.ObjectType, 
            self.ObjectGUID, 
            self.ObjectPlugin, 
            self.ObjectMAC, 
            self.ObjectIP, 
            self.ObjectPrimaryID, 
            self.ObjectSecondaryID, 
            self.ObjectForeignKey, 
            self.ObjectIndex, 
            self.ObjectRowID, 
            self.ObjectStatusColumn, 
            self.ObjectStatus, 
            self.AppEventStatus, 
            self.Extra
        ))

        self.save()

    def save(self):
        # Commit changes
        self.db.commitDB()

