
import subprocess

import conf
from const import logPath
from database import sql_nmap_scan_all
from helper import json_struc, timeNow, updateState
from logger import append_line_to_file, mylog
#-------------------------------------------------------------------------------



class nmap_entry:
    def __init__(self, mac, time, port, state, service, name = '', extra = '', index = 0):
        self.mac = mac
        self.time = time
        self.port = port
        self.state = state
        self.service = service
        self.name = name
        self.extra = extra
        self.index = index
        self.hash = str(mac) + str(port)+ str(state)+ str(service)


#-------------------------------------------------------------------------------
def performNmapScan(db, devicesToScan):
    sql = db.sql # TO-DO

    global changedPorts_json_struc     
    
    changedPortsTmp = []

    if len(devicesToScan) > 0:

        timeoutSec = conf.NMAP_TIMEOUT

        devTotal = len(devicesToScan)

        updateState(db,"Scan: Nmap")

        mylog('verbose', ['[', timeNow(), '] Scan: Nmap for max ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min) per device'])  

        mylog('verbose', ["        Estimated max delay: ", (devTotal * int(timeoutSec)), 's ', '(', round((devTotal * int(timeoutSec))/60,1) , 'min)' ])

        devIndex = 0
        for device in devicesToScan:
            # Execute command
            output = ""
            # prepare arguments from user supplied ones
            nmapArgs = ['nmap'] + conf.NMAP_ARGS.split() + [device["dev_LastIP"]]

            progress = ' (' + str(devIndex+1) + '/' + str(devTotal) + ')'

            try:
                # try runnning a subprocess with a forced (timeout + 30 seconds)  in case the subprocess hangs
                output = subprocess.check_output (nmapArgs, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec + 30))
            except subprocess.CalledProcessError as e:
                # An error occured, handle it
                mylog('none', [e.output])
                mylog('none', ["        Error - Nmap Scan - check logs", progress])            
            except subprocess.TimeoutExpired as timeErr:
                mylog('verbose', ['        Nmap TIMEOUT - the process forcefully terminated as timeout reached for ', device["dev_LastIP"], progress]) 

            if output == "": # check if the subprocess failed                    
                mylog('info', ['[', timeNow(), '] Scan: Nmap FAIL for ', device["dev_LastIP"], progress ,' check logs for details']) 
            else: 
                mylog('verbose', ['[', timeNow(), '] Scan: Nmap SUCCESS for ', device["dev_LastIP"], progress])

            devIndex += 1
            
            #  check the last run output        
            newLines = output.split('\n')

            # regular logging
            for line in newLines:
                append_line_to_file (logPath + '/pialert_nmap.log', line +'\n')                
            
            # collect ports / new Nmap Entries
            newEntriesTmp = []

            index = 0
            startCollecting = False
            duration = "" 
            for line in newLines:            
                if 'Starting Nmap' in line:
                    if len(newLines) > index+1 and 'Note: Host seems down' in newLines[index+1]:
                        break # this entry is empty
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                    startCollecting = True
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:    
                    startCollecting = False # end reached
                elif startCollecting and len(line.split()) == 3:                                    
                    newEntriesTmp.append(nmap_entry(device["dev_MAC"], timeNow(), line.split()[0], line.split()[1], line.split()[2], device["dev_Name"]))
                elif 'Nmap done' in line:
                    duration = line.split('scanned in ')[1]            
            index += 1

            # previous Nmap Entries
            oldEntries = []

            mylog('verbose', ['[', timeNow(), '] Scan: Ports found by NMAP: ', len(newEntriesTmp)])
            
            if len(newEntriesTmp) > 0:   

                #  get all current NMAP ports from the DB
                sql.execute(sql_nmap_scan_all) 

                rows = sql.fetchall()

                for row in rows: 
                    # only collect entries matching the current MAC address
                    if row["MAC"] == device["dev_MAC"]:
                        oldEntries.append(nmap_entry(row["MAC"], row["Time"], row["Port"], row["State"], row["Service"], device["dev_Name"], row["Extra"], row["Index"]))


                newEntries = []

                # Collect all entries that don't match the ones in the DB               
                for newTmpEntry in newEntriesTmp:

                    found = False
                    
                    #  Check the new entry is already available in oldEntries and remove from processing if yes
                    for oldEntry in oldEntries: 
                        if newTmpEntry.hash == oldEntry.hash:
                            found = True

                    if not found:
                        newEntries.append(newTmpEntry)


                mylog('verbose', ['[', timeNow(), '] Scan: Nmap newly discovered or changed ports: ', len(newEntries)])                

                # collect new ports, find the corresponding old entry and return for notification purposes
                # also update the DB with the new values after deleting the old ones
                if len(newEntries) > 0:
                    
                    # params to build the SQL query
                    params = []
                    indexesToDelete = ""

                    # Find old entry matching the new entry hash
                    for newEntry in newEntries:                   

                        foundEntry = None

                        for oldEntry in oldEntries:
                            if oldEntry.hash == newEntry.hash:
                                indexesToDelete = indexesToDelete + str(oldEntry.index) + ','
                                foundEntry = oldEntry                        

                        columnNames = ["Name", "MAC", "Port", "State", "Service", "Extra", "NewOrOld"  ]

                        # Old entry found
                        if foundEntry is not None:
                            # Build params for sql query
                            params.append((newEntry.mac, newEntry.time, newEntry.port, newEntry.state, newEntry.service, oldEntry.extra))
                            # Build JSON for API and notifications
                            changedPortsTmp.append({       
                                                    "Name"      : foundEntry.name, 
                                                    "MAC"       : newEntry.mac, 
                                                    "Port"      : newEntry.port, 
                                                    "State"     : newEntry.state, 
                                                    "Service"   : newEntry.service, 
                                                    "Extra"     : foundEntry.extra,
                                                    "NewOrOld"  : "New values"
                                                })
                            changedPortsTmp.append({ 
                                                    "Name"      : foundEntry.name, 
                                                    "MAC"       : foundEntry.mac, 
                                                    "Port"      : foundEntry.port, 
                                                    "State"     : foundEntry.state, 
                                                    "Service"   : foundEntry.service, 
                                                    "Extra"     : foundEntry.extra,
                                                    "NewOrOld"  : "Old values"
                                                })                            
                        # New entry - no matching Old entry found
                        else:
                            # Build params for sql query
                            params.append((newEntry.mac, newEntry.time, newEntry.port, newEntry.state, newEntry.service, ''))
                            # Build JSON for API and notifications
                            changedPortsTmp.append({
                                                    "Name"      : "New device", 
                                                    "MAC"       : newEntry.mac, 
                                                    "Port"      : newEntry.port, 
                                                    "State"     : newEntry.state, 
                                                    "Service"   : newEntry.service, 
                                                    "Extra"     : "",
                                                    "NewOrOld"  : "New device"                                       
                                                })

                    changedPorts_json_struc = json_struc({ "data" : changedPortsTmp}, columnNames)

                    #  Delete old entries if available
                    if len(indexesToDelete) > 0:
                        sql.execute ("DELETE FROM Nmap_Scan where \"Index\" in (" + indexesToDelete[:-1] +")")
                        db.commitDB()

                    # Insert new values into the DB 
                    sql.executemany ("""INSERT INTO Nmap_Scan ("MAC", "Time", "Port", "State", "Service", "Extra") VALUES (?, ?, ?, ?, ?, ?)""", params) 
                    db.commitDB()


