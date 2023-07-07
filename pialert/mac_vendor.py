
import subprocess
import conf

from const import pialertPath, vendorsDB
from helper import timeNow, updateState
from logger import mylog


#===============================================================================
# UPDATE DEVICE MAC VENDORS
#===============================================================================



def update_devices_MAC_vendors (db, pArg = ''):
    sql = db.sql # TO-DO
    # Header    
    updateState(db,"Upkeep: Vendors")
    mylog('verbose', ['[', timeNow(), '] Upkeep - Update HW Vendors:' ])

    # Update vendors DB (iab oui)
    mylog('verbose', ['    Updating vendors DB (iab & oui)'])    
    update_args = ['sh', pialertPath + '/update_vendors.sh', pArg]

    # Execute command
    if conf.LOG_LEVEL == 'debug':
        # try runnning a subprocess
        update_output = subprocess.check_output (update_args)
    else:    
        try:
            # try runnning a subprocess safely
            update_output = subprocess.check_output (update_args)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ['    FAILED: Updating vendors DB, set LOG_LEVEL=debug for more info'])  
            mylog('none', [e.output])        

    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    # All devices loop
    mylog('verbose', ['    Searching devices vendor'])    
    for device in sql.execute ("""SELECT * FROM Devices
                                  WHERE dev_Vendor = '(unknown)' 
                                     OR dev_Vendor =''
                                     OR dev_Vendor IS NULL""") :
        # Search vendor in HW Vendors DB
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor == -1 :
            notFound += 1
        elif vendor == -2 :
            ignored += 1
        else :
            recordsToUpdate.append ([vendor, device['dev_MAC']])
            
    # Print log    
    mylog('verbose', ["    Devices Ignored:  ", ignored])
    mylog('verbose', ["    Vendors Not Found:", notFound])
    mylog('verbose', ["    Vendors updated:  ", len(recordsToUpdate) ])


    # update devices
    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    # Commit DB
    db.commitDB()

    if len(recordsToUpdate) > 0:
        return True
    else:
        return False

#-------------------------------------------------------------------------------
def query_MAC_vendor (pMAC):
    try :
        # BUGFIX #6 - Fix pMAC parameter as numbers
        pMACstr = str(pMAC)
        
        # Check MAC parameter
        mac = pMACstr.replace (':','')
        if len(pMACstr) != 17 or len(mac) != 12 :
            return -2

        # Search vendor in HW Vendors DB
        mac = mac[0:6]
        grep_args = ['grep', '-i', mac, vendorsDB]
        
        # Execute command
        if conf.LOG_LEVEL == 'debug':
            # try runnning a subprocess
            grep_output = subprocess.check_output (grep_args)
        else:
            try:
                # try runnning a subprocess
                grep_output = subprocess.check_output (grep_args)
            except subprocess.CalledProcessError as e:
                # An error occured, handle it
                mylog('none', ["[Mac Vendor Check] Error: ", e.output])
                grep_output = "       There was an error, check logs for details"

        # Return Vendor
        vendor = grep_output[7:]
        vendor = vendor.rstrip()
        return vendor

    # not Found
    except subprocess.CalledProcessError :
        return -1
  
