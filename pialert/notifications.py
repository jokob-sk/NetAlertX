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
# Notification object handling
#-------------------------------------------------------------------------------
class Notifications:
    def __init__(self, db):
        self.db = db

        # Create Notifications table if missing        
        self.db.sql.execute("""CREATE TABLE IF NOT EXISTS "Notifications" (
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
        """)

        self.save()

    # Create a new DB entry if new notiifcations available, otherwise skip
    def create(self, JSON, Text, HTML, Extra=""):

        # Check if empty JSON
        # _json = json.loads(JSON)
        # Check if nothing to report
        if JSON["internet"] == [] and JSON["new_devices"] == [] and JSON["down_devices"] == [] and JSON["events"] == [] and JSON["plugins"] == []:
            self.HasNotifications = False
            # end if nothing to report
            return self.HasNotifications        

        #  continue and save into DB if notifications available
        self.HasNotifications = True 

        self.GUID               = str(uuid.uuid4())
        self.DateTimeCreated    = timeNowTZ()
        self.DateTimePushed     = ""
        self.Status             = "new"
        self.JSON               = JSON
        self.Text               = Text
        self.HTML               = HTML
        self.PublishedVia       = ""
        self.Extra              = Extra

        self.upsert()
        
        return self.HasNotifications

    # Only updates the status
    def updateStatus(self, newStatus):
        self.Status = newStatus
        self.upsert()

    # Updates the Published properties
    def updatePublishedVia(self, newPublishedVia):
        self.PublishedVia = newPublishedVia
        self.DateTimePushed = timeNowTZ()
        self.upsert()

        # TODO Index vs hash to minimize SQL calls, finish CRUD operations, expose via API, use API in plugins

    def upsert(self):
        self.db.sql.execute("""
            INSERT OR REPLACE INTO Notifications (GUID, DateTimeCreated, DateTimePushed, Status, JSON, Text, HTML, PublishedVia, Extra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.GUID, self.DateTimeCreated, self.DateTimePushed, self.Status, json.dumps(self.JSON), self.Text, self.HTML, self.PublishedVia, self.Extra))

        self.save()

    def save(self):
        # Commit changes
        self.db.commitDB()