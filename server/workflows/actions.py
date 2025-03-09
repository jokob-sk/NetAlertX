import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

import conf
from logger import mylog, Logger
from helper import get_setting_value, timeNowTZ

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

from workflows.triggers import Trigger

class Action:
    """Base class for all actions."""

    def __init__(self, trigger):        
        self.trigger = trigger    

    def execute(self, obj):
        """Executes the action on the given object."""
        raise NotImplementedError("Subclasses must implement execute()")


class UpdateFieldAction(Action):
    """Action to update a specific field of an object."""

    def __init__(self, field, value, trigger):
        super().__init__(trigger)  # Call the base class constructor
        self.field = field
        self.value = value

    def execute(self):
        mylog('verbose', [f"Updating field '{self.field}' to '{self.value}' for event object {self.trigger.object_type}"])

        obj = self.trigger.object

        if isinstance(obj, dict) and "ObjectGUID" in obj:
            plugin_instance = PluginObjectInstance(self.trigger.db)
            plugin_instance.updateField(obj["ObjectGUID"], self.field, self.value)
        elif isinstance(obj, dict) and "devGUID" in obj:
            device_instance = DeviceInstance(self.trigger.db)
            device_instance.updateField(obj["devGUID"], self.field, self.value)
        return obj


class RunPluginAction(Action):
    """Action to run a specific plugin."""

    def __init__(self, plugin_name, params, trigger):  # Add trigger
        super().__init__(trigger)  # Call parent constructor
        self.plugin_name = plugin_name
        self.params = params

    def execute(self):
        
        obj = self.trigger.object

        mylog('verbose', [f"Executing plugin '{self.plugin_name}' with parameters {self.params} for object {obj}"])
        # PluginManager.run(self.plugin_name, self.parameters)
        return obj


class SendNotificationAction(Action):
    """Action to send a notification."""

    def __init__(self, method, message, trigger):
        super().__init__(trigger)  # Call parent constructor
        self.method = method  # Fix attribute name
        self.message = message

    def execute(self):
        obj = self.trigger.object
        mylog('verbose', [f"Sending notification via '{self.method}': {self.message} for object {obj}"])
        # NotificationManager.send(self.method, self.message)
        return obj


class ActionGroup:
    """Handles multiple actions applied to an object."""

    def __init__(self, actions):
        self.actions = actions

    def execute(self, obj):
        for action in self.actions:
            action.execute(obj)
        return obj