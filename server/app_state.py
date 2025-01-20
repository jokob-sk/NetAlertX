import os
import json

import conf
from const import *
from logger import mylog, logResult
from helper import timeNowTZ, timeNow, checkNewVersion

# Register NetAlertX directories
INSTALL_PATH="/app"


#-------------------------------------------------------------------------------
# App state
#-------------------------------------------------------------------------------
# A class to manage the application state and to provide a frontend accessible API point
# To keep an existing value pass None
class app_state_class:
    def __init__(self, currentState = None, settingsSaved=None, settingsImported=None, showSpinner=False, graphQLServerStarted=0, processScan=False):
        # json file containing the state to communicate with the frontend
        stateFile = apiPath + 'app_state.json'
        previousState = ""

        # Update self
        self.lastUpdated = str(timeNowTZ())
        
        if os.path.exists(stateFile):
            try:            
                with open(stateFile, 'r') as json_file:
                    previousState            = json.load(json_file)
            except json.decoder.JSONDecodeError as e:
                mylog('none', [f'[app_state_class] Failed to handle app_state.json: {e}'])                 

        # Check if the file exists and recover previous values
        if previousState != "":            
            self.settingsSaved          = previousState.get("settingsSaved", 0)
            self.settingsImported       = previousState.get("settingsImported", 0)
            self.processScan            = previousState.get("processScan", False)
            self.showSpinner            = previousState.get("showSpinner", False)
            self.isNewVersion           = previousState.get("isNewVersion", False)
            self.isNewVersionChecked    = previousState.get("isNewVersionChecked", 0)
            self.graphQLServerStarted   = previousState.get("graphQLServerStarted", 0)
            self.currentState           = previousState.get("currentState", "Init")
        else: # init first time values
            self.settingsSaved          = 0
            self.settingsImported       = 0
            self.showSpinner            = False
            self.processScan            = False
            self.isNewVersion           = checkNewVersion()
            self.isNewVersionChecked    = int(timeNow().timestamp())
            self.graphQLServerStarted   = 0
            self.currentState           = "Init"

        # Overwrite with provided parameters if supplied
        if settingsSaved is not None:
            self.settingsSaved = settingsSaved
        if settingsImported is not None:
            self.settingsImported = settingsImported
        if showSpinner is not None:
            self.showSpinner = showSpinner
        if graphQLServerStarted is not None:
            self.graphQLServerStarted = graphQLServerStarted
        if processScan is not None:
            self.processScan = processScan
        if currentState is not None:
            self.currentState = currentState

        # check for new version every hour and if currently not running new version
        if self.isNewVersion is False and self.isNewVersionChecked + 3600 < int(timeNow().timestamp()):
            self.isNewVersion           = checkNewVersion()
            self.isNewVersionChecked    = int(timeNow().timestamp())

        # Update .json file
        # with open(stateFile, 'w') as json_file:
        #     json.dump(self, json_file, cls=AppStateEncoder, indent=4)
            
         # Remove lastUpdated from the dictionary for comparison
        currentStateDict = self.__dict__.copy()
        currentStateDict.pop('lastUpdated', None)

        # Compare current state with previous state before updating
        if previousState != currentStateDict:
            # Sanity check before saving the .json file
            try:
                json_data = json.dumps(self, cls=AppStateEncoder, indent=4)
                with open(stateFile, 'w') as json_file:
                    json_file.write(json_data)
            except (TypeError, ValueError) as e:
                mylog('none', [f'[app_state_class] Failed to serialize object to JSON: {e}'])   

        return  # Allows chaining by returning self     



#-------------------------------------------------------------------------------
# method to update the state
def updateState(newState = None, settingsSaved = None, settingsImported = None, showSpinner = False, graphQLServerStarted = None, processScan = None):

    return app_state_class(newState, settingsSaved, settingsImported, showSpinner, graphQLServerStarted, processScan)


#-------------------------------------------------------------------------------
# Checks if the object has a __dict__ attribute. If it does, it assumes that it's an instance of a class and serializes its attributes dynamically. 
class AppStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            # If the object has a '__dict__', assume it's an instance of a class
            return obj.__dict__
        return super().default(obj)