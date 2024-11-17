import graphene
from graphene import ObjectType, String, Int, Boolean, List, Field, InputObjectType
import json
import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from const import apiPath
from helper import is_random_mac, get_number_of_children, format_ip_long, get_setting_value

# Define a base URL with the user's home directory
folder = apiPath 

# Pagination and Sorting Input Types
class SortOptionsInput(InputObjectType):
    field = String()
    order = String()

class PageQueryOptionsInput(InputObjectType):
    page = Int()
    limit = Int()
    sort = List(SortOptionsInput)
    search = String()
    status = String()

# Device ObjectType
class Device(ObjectType):
    rowid = Int()
    devMac = String()  
    devName = String()  
    devOwner = String() 
    devType = String()  
    devVendor = String()  
    devFavorite = Int()  
    devGroup = String()  
    devComments = String() 
    devFirstConnection = String() 
    devLastConnection = String() 
    devLastIP = String() 
    devStaticIP = Int()  
    devScan = Int()  
    devLogEvents = Int() 
    devAlertEvents = Int() 
    devAlertDown = Int()  
    devSkipRepeated = Int() 
    devLastNotification = String() 
    devPresentLastScan = Int() 
    devIsNew = Int()  
    devLocation = String() 
    devIsArchived = Int() 
    devParentMAC = String()  
    devParentPort = String()  
    devIcon = String() 
    devGUID = String() 
    devSite = String() 
    devSSID = String() 
    devSyncHubNode = String() 
    devSourcePlugin = String()
    devStatus = String()
    devIsRandomMac = Int()  
    devParentChildrenCount = Int() 
    devIpLong = Int() 
    devFilterStatus = String() 


class DeviceResult(ObjectType):
    devices = List(Device)
    count = Int()

# Define Query Type with Pagination Support
class Query(ObjectType):
    devices = Field(DeviceResult, options=PageQueryOptionsInput())

    def resolve_devices(self, info, options=None):
        # mylog('none', f'[graphql_schema] resolve_devices: {self}')
        try:
            with open(folder + 'table_devices.json', 'r') as f:
                devices_data = json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            mylog('none', f'[graphql_schema] Error loading devices data: {e}')
            return DeviceResult(devices=[], count=0)


        # Add dynamic fields to each device
        for device in devices_data:
            device["devIsRandomMac"] = 1 if is_random_mac(device["devMac"]) else 0
            device["devParentChildrenCount"] = get_number_of_children(device["devMac"], devices_data)
            device["devIpLong"] = format_ip_long(device.get("devLastIP", ""))

        total_count = len(devices_data)

        mylog('none', f'[graphql_schema] devices_data: {devices_data}')



        # Apply sorting if options are provided
        if options:

            # Define status-specific filtering
            if options.status:
                status = options.status
                mylog('none', f'[graphql_schema] Applying status filter: {status}')

                # Example filtering based on the "status"
                if status == "my_devices":
                    # Include devices matching criteria in UI_MY_DEVICES
                    allowed_statuses = get_setting_value("UI_MY_DEVICES")  

                    mylog('none', f'[graphql_schema] allowed_statuses: {allowed_statuses}')

                    devices_data = [
                        device for device in devices_data
                        if (
                            (device["devPresentLastScan"] == 1 and 'online' in allowed_statuses) or
                            (device["devIsNew"] == 1 and 'new' in allowed_statuses) or
                            (device["devPresentLastScan"] == 0 and device["devAlertDown"] and 'down' in allowed_statuses) or
                            (device["devPresentLastScan"] == 0 and 'offline' in allowed_statuses)
                        )
                    ]
                elif status == "connected":
                    devices_data = [device for device in devices_data if device["devPresentLastScan"] == 1]
                elif status == "favorites":
                    devices_data = [device for device in devices_data if device["devFavorite"] == 1]
                elif status == "new":
                    devices_data = [device for device in devices_data if device["devIsNew"] == 1]
                elif status == "down":
                    devices_data = [
                        device for device in devices_data 
                        if device["devPresentLastScan"] == 0 and device["devAlertDown"]
                    ]
                elif status == "archived":
                    devices_data = [device for device in devices_data if device["devIsArchived"] == 1]
                elif status == "offline":
                    devices_data = [device for device in devices_data if device["devPresentLastScan"] == 0]

            # sorting
            if options.sort:
                for sort_option in options.sort:
                    devices_data = sorted(
                        devices_data,
                        key=lambda x: mixed_type_sort_key(x.get(sort_option.field)),
                        reverse=(sort_option.order.lower() == "desc")
                    )

            # Filter data if a search term is provided
            if options.search:
                # Define static list of searchable fields
                searchable_fields = [
                    "devName", "devMac", "devOwner", "devType", "devVendor", 
                    "devGroup", "devComments", "devLocation", "devStatus",
                    "devSSID", "devSite", "devSourcePlugin", "devSyncHubNode"
                ]

                search_term = options.search.lower()

                devices_data = [
                    device for device in devices_data
                    if any(
                        search_term in str(device.get(field, "")).lower()
                        for field in searchable_fields  # Search only predefined fields
                    )
                ]

            # Then apply pagination
            if options.page and options.limit:
                start = (options.page - 1) * options.limit
                end = start + options.limit
                devices_data = devices_data[start:end]

        # Convert dict objects to Device instances to enable field resolution
        devices = [Device(**device) for device in devices_data]

        return DeviceResult(devices=devices, count=total_count)

# helps sorting inconsistent dataset mixed integers and strings
def mixed_type_sort_key(value):
    if value is None or value == "":
        return (2, '')  # Place None or empty strings last
    try:
        return (0, int(value))  # Integers get priority
    except (ValueError, TypeError):
        return (1, str(value))  # Strings come next

# Schema Definition
devicesSchema = graphene.Schema(query=Query)
