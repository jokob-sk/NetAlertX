import graphene
from graphene import ObjectType, String, Int, Boolean, Field, List
import json
import sys


# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from const import apiPath

# Define a base URL with the user's home directory
folder = apiPath 

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


class Query(ObjectType):
    devices = List(Device)

    def resolve_devices(self, info):
        # Load JSON data only when the query executes
        try:
            with open(folder + 'table_devices.json', 'r') as f:
                devices_data = json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            mylog('error', f'[graphql_schema] Error loading devices data: {e}')
            return []

        return devices_data  # Directly return the data without mapping



# Schema Definition
devicesSchema = graphene.Schema(query=Query)

# # Sample query
# $.ajax({
#     url: 'php/server/query_graphql.php', // The PHP endpoint that proxies to the GraphQL server
#     type: 'POST',
#     contentType: 'application/json', // Send the data as JSON
#     data: JSON.stringify({
#         query: `
#             query {
#               devices {
#                 devMac
#                 devName
#                 devLastConnection
#                 devArchived
#               }
#             }
#         `, // GraphQL query for plugins
#         variables: {} // Optional, pass variables if needed
#     }),
#     success: function(response) {
#         console.log('GraphQL Response:', response);
#         // Handle the GraphQL response here
#     },
#     error: function(xhr, status, error) {
#         console.error('AJAX Error:', error);
#         // Handle errors here
#     }
# });
