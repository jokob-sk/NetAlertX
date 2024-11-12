import graphene
from graphene import ObjectType, String, Int, Boolean, List, Field, InputObjectType
import json
import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from const import apiPath

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

class DeviceResult(ObjectType):
    devices = List(Device)
    count = Int()

# Define Query Type with Pagination Support
class Query(ObjectType):
    devices = Field(DeviceResult, options=PageQueryOptionsInput())

    def resolve_devices(self, info, options=None):
        try:
            with open(folder + 'table_devices.json', 'r') as f:
                devices_data = json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            mylog('none', f'[graphql_schema] Error loading devices data: {e}')
            return DeviceResult(devices=[], count=0)

        total_count = len(devices_data)

        # Apply pagination and sorting if options are provided
        if options:
            # Implement pagination and sorting here
            if options.page and options.limit:
                start = (options.page - 1) * options.limit
                end = start + options.limit
                devices_data = devices_data[start:end]

            if options.sort:
                for sort_option in options.sort:
                    devices_data = sorted(
                        devices_data,
                        key=lambda x: x.get(sort_option.field),
                        reverse=(sort_option.order.lower() == "desc")
                    )
                
            # Filter data if a search term is provided
            if options.search:
                devices_data = [
                    device for device in devices_data
                    if options.search.lower() in device.get("devName", "").lower()
                ]

        return DeviceResult(devices=devices_data, count=total_count)


# Schema Definition
devicesSchema = graphene.Schema(query=Query)
