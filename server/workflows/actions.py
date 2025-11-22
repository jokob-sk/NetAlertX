import sqlite3
from logger import mylog, Logger
from helper import get_setting_value
from models.device_instance import DeviceInstance
from models.plugin_object_instance import PluginObjectInstance

# Make sure log level is initialized correctly
Logger(get_setting_value("LOG_LEVEL"))


class Action:
    """Base class for all actions."""

    def __init__(self, trigger):
        self.trigger = trigger

    def execute(self, obj):
        """Executes the action on the given object."""
        raise NotImplementedError("Subclasses must implement execute()")


class UpdateFieldAction(Action):
    """Action to update a specific field of an object."""

    def __init__(self, db, field, value, trigger):
        super().__init__(trigger)  # Call the base class constructor
        self.field = field
        self.value = value
        self.db = db

    def execute(self):
        mylog(
            "verbose",
            f"[WF] Updating field '{self.field}' to '{self.value}' for event object {self.trigger.object_type}",
        )

        obj = self.trigger.object

        # convert to dict for easeir handling
        if isinstance(obj, sqlite3.Row):
            obj = dict(obj)  # Convert Row object to a standard dictionary

        processed = False

        # currently unused
        if isinstance(obj, dict) and "ObjectGUID" in obj:
            mylog("debug", f"[WF] Updating Object '{obj}' ")
            plugin_instance = PluginObjectInstance(self.db)
            plugin_instance.updateField(obj["ObjectGUID"], self.field, self.value)
            processed = True

        elif isinstance(obj, dict) and "devGUID" in obj:
            mylog("debug", f"[WF] Updating Device '{obj}' ")
            device_instance = DeviceInstance(self.db)
            device_instance.updateField(obj["devGUID"], self.field, self.value)
            processed = True

        if not processed:
            mylog("none", f"[WF] Could not process action for object: {obj}")

        return obj


class DeleteObjectAction(Action):
    """Action to delete an object."""

    def __init__(self, db, trigger):
        super().__init__(trigger)  # Call the base class constructor
        self.db = db

    def execute(self):
        mylog("verbose", f"[WF] Deleting event object {self.trigger.object_type}")

        obj = self.trigger.object

        # convert to dict for easeir handling
        if isinstance(obj, sqlite3.Row):
            obj = dict(obj)  # Convert Row object to a standard dictionary

        processed = False

        # currently unused
        if isinstance(obj, dict) and "ObjectGUID" in obj:
            mylog("debug", f"[WF] Updating Object '{obj}' ")
            plugin_instance = PluginObjectInstance(self.db)
            plugin_instance.delete(obj["ObjectGUID"])
            processed = True

        elif isinstance(obj, dict) and "devGUID" in obj:
            mylog("debug", f"[WF] Updating Device '{obj}' ")
            device_instance = DeviceInstance(self.db)
            device_instance.delete(obj["devGUID"])
            processed = True

        if not processed:
            mylog("none", f"[WF] Could not process action for object: {obj}")

        return obj


class RunPluginAction(Action):
    """Action to run a specific plugin."""

    def __init__(self, plugin_name, params, trigger):  # Add trigger
        super().__init__(trigger)  # Call parent constructor
        self.plugin_name = plugin_name
        self.params = params

    def execute(self):
        obj = self.trigger.object

        mylog(
            "verbose",
            [
                f"Executing plugin '{self.plugin_name}' with parameters {self.params} for object {obj}"
            ],
        )
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
        mylog(
            "verbose",
            [
                f"Sending notification via '{self.method}': {self.message} for object {obj}"
            ],
        )
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
