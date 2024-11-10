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

# Load your JSON data
with open(folder + 'table_devices.json', 'r') as f:
    devices_data = json.load(f)["data"]
    
    # mylog('none', [f'[graphql_schema] devices_data {devices_data}'])

# Device ObjectType
class Device(ObjectType):
    rowid = Int()
    devMac = String()  # This should match devMac, not devMac
    devName = String()  # This should match devName, not devName
    devOwner = String()  # This should match devOwner, not devOwner
    devType = String()  # This should match devType, not devType
    devVendor = String()  # This should match devVendor, not devVendor
    devFavorite = Int()  # This should match devFavorite, not devFavorite
    devGroup = String()  # This should match devGroup, not devGroup
    devComments = String()  # This should match devComments, not devComments
    devFirstConnection = String()  # This should match devFirstConnection, not devFirstConnection
    devLastConnection = String()  # This should match devLastConnection, not devLastConnection
    devLastIP = String()  # This should match devLastIP, not devLastIP
    devStaticIP = Int()  # This should match devStaticIP, not devStaticIP
    devScan = Int()  # This should match devScan, not devScan
    devLogEvents = Int()  # This should match devLogEvents, not devLogEvents
    devAlertEvents = Int()  # This should match devAlertEvents, not devAlertEvents
    devAlertDeviceDown = Int()  # This should match devAlertDeviceDown, not devAlertDown
    devSkipRepeated = Int()  # This should match devSkipRepeated, not devSkipRepeated
    devLastNotification = String()  # This should match devLastNotification, not devLastNotification
    devPresentLastScan = Int()  # This should match devPresentLastScan, not devPresentLastScan
    devNewDevice = Int()  # This should match devNewDevice, not devIsNew
    devLocation = String()  # This should match devLocation, not devLocation
    devArchived = Int()  # This should match devArchived, not devIsArchived
    devNetworkNodeMACADDR = String()  # This should match devNetworkNodeMACADDR, not devParentMAC
    devNetworkNodePort = String()  # This should match devNetworkNodePort, not devParentPort
    devIcon = String()  # This should match devIcon, not devIcon
    devGUID = String()  # This should match devGUID, not devGUID
    devNetworkSite = String()  # This should match devNetworkSite, not devSite
    devSSID = String()  # This should match devSSID, not devSSID
    devSyncHubNodeName = String()  # This should match devSyncHubNodeName, not devSyncHubNode
    devSourcePlugin = String()  # This should match devSourcePlugin, not devSourcePlugin


# Query ObjectType
class Query(ObjectType):
    devices = List(Device)

    def resolve_devices(self, info):
        # Map the data to match the GraphQL schema's camelCase
        mapped_devices = []
        for device in devices_data:
            mapped_device = {
                'rowid': device['rowid'],
                'devMac': device['devMac'],  # Mapping from snake_case to camelCase
                'devName': device['devName'],
                'devOwner': device['devOwner'],
                'devType': device['devType'],
                'devVendor': device['devVendor'],
                'devFavorite': device['devFavorite'],
                'devGroup': device['devGroup'],
                'devComments': device['devComments'],
                'devFirstConnection': device['devFirstConnection'],
                'devLastConnection': device['devLastConnection'],
                'devLastIP': device['devLastIP'],
                'devStaticIP': device['devStaticIP'],
                'devScan': device['devScan'],
                'devLogEvents': device['devLogEvents'],
                'devAlertEvents': device['devAlertEvents'],
                'devAlertDown': device['devAlertDown'],
                'devSkipRepeated': device['devSkipRepeated'],
                'devLastNotification': device['devLastNotification'],
                'devPresentLastScan': device['devPresentLastScan'],
                'devIsNew': device['devIsNew'],
                'devLocation': device['devLocation'],
                'devIsArchived': device['devIsArchived'],
                'devParentMAC': device['devParentMAC'],
                'devParentPort': device['devParentPort'],
                'devIcon': device['devIcon'],
                'devGUID': device['devGUID'],
                'devSite': device['devSite'],
                'devSSID': device['devSSID'],
                'devSyncHubNode': device['devSyncHubNode'],
                'devSourcePlugin': device['devSourcePlugin']
            }
            mapped_devices.append(mapped_device)
        return mapped_devices


# Schema Definition
devicesSchema = graphene.Schema(query=Query)


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
