#!/bin/sh
echo "Create backup before insert new table"
cp ../db/pialert.db ../db/pialert.db.bak
echo "Insert new table 'Online_History' to pialert.db"
sqlite3 ../db/pialert.db  "CREATE TABLE 'Online_History' ('Index' INTEGER, 'Scan_Date' TEXT, 'Online_Devices' INTEGER, 'Down_Devices' INTEGER, 'All_Devices' INTEGER, 'Archived_Devices' INTEGER, PRIMARY KEY('Index' AUTOINCREMENT));"
