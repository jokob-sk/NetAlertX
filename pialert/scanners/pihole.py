""" module to import db and leases from PiHole """
# TODO remove this file in teh future

import sqlite3

import conf
from logger import mylog

piholeDhcpleases       = '/etc/pihole/dhcp.leases'
piholeDB               = '/etc/pihole/pihole-FTL.db'

#-------------------------------------------------------------------------------
def copy_pihole_network (db):
    """
    attach the PiHole Database and copy the PiHole_Network table accross into the PiAlert DB
    """
    
    sql = db.sql # TO-DO
    # Open Pi-hole DB
    mylog('debug', '[PiHole Network] - attach PiHole DB')

    try:
        sql.execute ("ATTACH DATABASE '"+ piholeDB +"' AS PH")
    except sqlite3.Error as e:
        mylog('none',[ '[PiHole Network] - SQL ERROR: ', e])
    

    # Copy Pi-hole Network table

    try:
        sql.execute ("DELETE FROM PiHole_Network")

        # just for reporting
        new_devices = []        
        sql.execute ( """SELECT hwaddr, macVendor, lastQuery,
                        (SELECT name FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip),
                        (SELECT ip FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip)
                    FROM PH.network
                    WHERE hwaddr NOT LIKE 'ip-%'
                      AND hwaddr <> '00:00:00:00:00:00' """)
        new_devices = sql.fetchall()

        # insert into PiAlert DB
        sql.execute ("""INSERT INTO PiHole_Network (PH_MAC, PH_Vendor, PH_LastQuery,
                        PH_Name, PH_IP)
                    SELECT hwaddr, macVendor, lastQuery,
                        (SELECT name FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip),
                        (SELECT ip FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip)
                    FROM PH.network
                    WHERE hwaddr NOT LIKE 'ip-%'
                      AND hwaddr <> '00:00:00:00:00:00' """)
        sql.execute ("""UPDATE PiHole_Network SET PH_Name = '(unknown)'
                    WHERE PH_Name IS NULL OR PH_Name = '' """)
        # Close Pi-hole DB
        sql.execute ("DETACH PH")

    except sqlite3.Error as e:
        mylog('none',[ '[PiHole Network] - SQL ERROR: ', e])
    
    db.commitDB()
    
    mylog('debug',[ '[PiHole Network] - completed - found ', len(new_devices), ' devices'])
    return str(sql.rowcount) != "0"


#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def read_DHCP_leases (db):
    """
    read the PiHole DHCP file and insert all records into the DHCP_Leases table.
    """ 
    mylog('debug', '[PiHole DHCP] - read DHCP_Leases file')
    # Read DHCP Leases
    # Bugfix #1 - dhcp.leases: lines with different number of columns (5 col)
    data = []
    reporting = False
    with open(piholeDhcpleases, 'r') as f:
        for line in f:
            reporting = True
            row = line.rstrip().split()
            if len(row) == 5 :
                data.append (row)

    # Insert into PiAlert table    
    db.sql.executemany ("""INSERT INTO DHCP_Leases (DHCP_DateTime, DHCP_MAC,
                            DHCP_IP, DHCP_Name, DHCP_MAC2)
                        VALUES (?, ?, ?, ?, ?)
                     """, data)
    db.commitDB()

    mylog('debug', ['[PiHole DHCP] - completed - added ',len(data), ' devices.'])
    return reporting