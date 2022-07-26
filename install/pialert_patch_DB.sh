#!/bin/sh
DB_NAME="pialert.db"
echo "Create backup before insert new table"
cp ../db/$DB_NAME ../db/pialert.db.bak
echo "Insert new table 'Online_History' to $DB_NAME"
sqlite3 ../db/$DB_NAME "CREATE TABLE 'Online_History' ('Index' INTEGER, 'Scan_Date' TEXT, 'Online_Devices' INTEGER, 'Down_Devices' INTEGER, 'All_Devices' INTEGER, 'Archived_Devices' INTEGER, PRIMARY KEY('Index' AUTOINCREMENT));"

