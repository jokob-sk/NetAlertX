import sys
import pathlib
import sqlite3
import random
import string
import uuid 
from datetime import datetime, timedelta

sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()) + "/server/")

from helper import timeNow, timeNowTZ, updateSubnets

# -------------------------------------------------------------------------------
def test_helper():
    assert timeNow() == datetime.now().replace(microsecond=0)

# -------------------------------------------------------------------------------
def test_updateSubnets():
    # test single subnet
    subnet = "192.168.1.0/24 --interface=eth0"
    result = updateSubnets(subnet)
    assert type(result) is list
    assert len(result) == 1

    # test multiple subnets
    subnet = ["192.168.1.0/24 --interface=eth0", "192.168.2.0/24 --interface=eth1"]
    result = updateSubnets(subnet)
    assert type(result) is list
    assert len(result) == 2

# -------------------------------------------------------------------------------
# Function to insert N random device entries
def insert_devices(db_path, num_entries=1):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"{num_entries} entries to generate.")

    # Function to generate a random MAC address
    def generate_mac():
        return '00:1A:2B:{:02X}:{:02X}:{:02X}'.format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Function to generate a random string of given length
    def generate_random_string(length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    # Function to generate a random date within the last `n` days
    def generate_random_date(n_days=365):
        start_date = datetime.now() - timedelta(days=random.randint(0, n_days))
        return start_date.strftime('%Y-%m-%d %H:%M:%S')

    # Function to generate a GUID (Globally Unique Identifier)
    def generate_guid():
        return str(uuid.uuid4())  # Generates a unique GUID

    # SQL query to insert a new row into Devices table
    insert_query = """
    INSERT INTO Devices (
        devMac, 
        devName, 
        devOwner, 
        devType, 
        devVendor, 
        devFavorite, 
        devGroup, 
        devComments, 
        devFirstConnection, 
        devLastConnection, 
        devLastIP, 
        devStaticIP, 
        devScan, 
        devLogEvents, 
        devAlertEvents, 
        devAlertDown, 
        devSkipRepeated, 
        devLastNotification, 
        devPresentLastScan, 
        devIsNew, 
        devLocation, 
        devIsArchived, 
        devParentMAC, 
        devParentPort, 
        devIcon, 
        devGUID, 
        devSite, 
        devSSID, 
        devSyncHubNode, 
        devSourcePlugin,
        devCustomProps,
        devFQDN
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    # List of device types, vendors, groups, locations
    device_types = ['Phone', 'Laptop', 'Tablet', 'Other']
    vendors = ['Vendor A', 'Vendor B', 'Vendor C']
    groups = ['Group1', 'Group2']
    locations = ['Location A', 'Location B']

    # Insert the specified number of rows (default is 10,000)
    for i in range(num_entries):
        dev_mac = generate_mac()
        dev_name = f'Device_{i:04d}'
        dev_owner = f'Owner_{i % 100:03d}'
        dev_type = random.choice(device_types)
        dev_vendor = random.choice(vendors)
        dev_favorite = random.choice([0, 1])
        dev_group = random.choice(groups)
        dev_comments = ""  # Left as NULL
        dev_first_connection = generate_random_date(365)  # Within last 365 days
        dev_last_connection = generate_random_date(30)  # Within last 30 days
        dev_last_ip = f'192.168.0.{random.randint(0, 255)}'
        dev_static_ip = random.choice([0, 1])
        dev_scan = random.randint(1, 10)
        dev_log_events = random.choice([0, 1])
        dev_alert_events = random.choice([0, 1])
        dev_alert_down = random.choice([0, 1])
        dev_skip_repeated = random.randint(0, 5)
        dev_last_notification = ""  # Left as NULL
        dev_present_last_scan = random.choice([0, 1])
        dev_is_new = random.choice([0, 1])
        dev_location = random.choice(locations)
        dev_is_archived = random.choice([0, 1])
        dev_parent_mac = ""  # Left as NULL
        dev_parent_port = ""  # Left as NULL
        dev_icon = ""  # Left as NULL
        dev_guid = generate_guid()  # Left as NULL
        dev_site = ""  # Left as NULL
        dev_ssid = ""  # Left as NULL
        dev_sync_hub_node = ""  # Left as NULL
        dev_source_plugin = ""  # Left as NULL
        dev_devCustomProps = ""  # Left as NULL
        dev_devFQDN = ""  # Left as NULL

        # Execute the insert query
        cursor.execute(insert_query, (
            dev_mac, 
            dev_name, 
            dev_owner, 
            dev_type, 
            dev_vendor, 
            dev_favorite, 
            dev_group, 
            dev_comments, 
            dev_first_connection, 
            dev_last_connection, 
            dev_last_ip, 
            dev_static_ip, 
            dev_scan, 
            dev_log_events, 
            dev_alert_events, 
            dev_alert_down, 
            dev_skip_repeated, 
            dev_last_notification, 
            dev_present_last_scan, 
            dev_is_new, 
            dev_location, 
            dev_is_archived, 
            dev_parent_mac, 
            dev_parent_port, 
            dev_icon, 
            dev_guid, 
            dev_site, 
            dev_ssid, 
            dev_sync_hub_node, 
            dev_source_plugin,
            dev_devCustomProps,
            dev_devFQDN
        ))

        # Commit after every 1000 rows to improve performance
        if i % 1000 == 0:
            conn.commit()

    # Final commit to save all remaining data
    conn.commit()

    # Close the database connection
    conn.close()

    print(f"{num_entries} entries have been successfully inserted into the Devices table.")

# -------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call insert_devices with database path and number of entries as arguments
    db_path = "/app/db/app.db"
    num_entries = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    insert_devices(db_path, num_entries)
