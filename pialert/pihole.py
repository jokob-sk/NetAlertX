from const import piholeDB, piholeDhcpleases

#-------------------------------------------------------------------------------
def copy_pihole_network (db):
    """
    attach the PiHole Database and copy the PiHole_Network table accross into the PiAlert DB
    """
    
    sql = db.sql # TO-DO
    # Open Pi-hole DB
    sql.execute ("ATTACH DATABASE '"+ piholeDB +"' AS PH")

    # Copy Pi-hole Network table
    sql.execute ("DELETE FROM PiHole_Network")
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
    db.commit()

    return str(sql.rowcount) != "0"

#-------------------------------------------------------------------------------
def read_DHCP_leases (db):
    """
    read the PiHole DHCP file and insert all records into the DHCP_Leases table.
    """

    sql = db.sql # TO-DO    
    # Read DHCP Leases
    # Bugfix #1 - dhcp.leases: lines with different number of columns (5 col)
    data = []
    with open(piholeDhcpleases, 'r') as f:
        for line in f:
            reporting = True
            row = line.rstrip().split()
            if len(row) == 5 :
                data.append (row)

    # Insert into PiAlert table    
    sql.executemany ("""INSERT INTO DHCP_Leases (DHCP_DateTime, DHCP_MAC,
                            DHCP_IP, DHCP_Name, DHCP_MAC2)
                        VALUES (?, ?, ?, ?, ?)
                     """, data)
    db.commit()
