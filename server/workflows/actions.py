import sqlite3
from logger import mylog, Logger
from helper import get_setting_value
from server.plugins.plugin_helper import normalize_mac
from models.device_instance import DeviceInstance
from models.plugin_object_instance import PluginObjectInstance
from workflows.constants import BOOLEAN_COLUMNS, TOKEN_RE

# Make sure log level is initialized correctly
Logger(get_setting_value("LOG_LEVEL"))


def interpolate_tokens(value, trigger_device):
    """Replace every ``{{trigger.COLUMN}}`` placeholder in *value* with the
    corresponding field from *trigger_device* (a plain dict).

    Unknown columns are left as-is so callers can log them separately.
    """
    if not isinstance(value, str):
        return value

    def _replace(match):
        col = match.group(1)
        return str(trigger_device.get(col, match.group(0)))

    return TOKEN_RE.sub(_replace, value)


class Action:
    """Base class for all actions."""

    def __init__(self, trigger):
        self.trigger = trigger

    def get_object(self):
        """Safely get and normalize the trigger object."""
        obj = getattr(self.trigger, "object", None)

        if isinstance(obj, sqlite3.Row):
            obj = dict(obj)

        return obj

    def execute(self):
        raise NotImplementedError("Subclasses must implement execute()")


class UpdateFieldAction(Action):
    """Action to update a specific field of a device.

    When *target_device* is supplied the action operates on that device rather
    than the one that raised the event, enabling cross-device targeting (v2).
    *trigger* is still required for context / logging.
    """

    def __init__(self, db, field, value, trigger, target_device=None):
        super().__init__(trigger)
        self.field = field
        self.value = value
        self.db = db
        self.target_device = target_device

    def execute(self):
        # Resolve the device to operate on
        obj = self.target_device if self.target_device is not None else self.get_object()

        if isinstance(obj, sqlite3.Row):
            obj = dict(obj)

        if obj is None:
            mylog("none", "[WF] UpdateFieldAction: target device no longer exists")
            return None

        # Interpolate {{trigger.X}} tokens in the value using the triggering device
        trigger_obj = self.get_object() or {}
        final_value = interpolate_tokens(self.value, trigger_obj)

        # Cast to int for boolean CHECK columns to satisfy SQLite constraints
        if self.field in BOOLEAN_COLUMNS:
            try:
                final_value = int(final_value)
            except (ValueError, TypeError):
                mylog("none", [f"[WF] Cannot cast value '{final_value}' to int for boolean field '{self.field}' — skipping"])
                return None

        mylog("verbose", f"[WF] Updating field '{self.field}' to '{final_value}' on device {obj.get('devGUID', '?')}")

        if "objectGuid" in obj:
            mylog("debug", f"[WF] Updating Object '{obj}'")
            PluginObjectInstance().updateField(obj["objectGuid"], self.field, final_value)
            return obj

        if "devGUID" in obj:
            # Guard: if mutating devMac, normalize the value and archive any
            # existing device already holding that MAC before writing to avoid
            # a PK UNIQUE constraint violation.
            if self.field == "devMac":
                final_value = normalize_mac(final_value)
                self._archive_conflicting_mac(final_value, obj["devGUID"])

            mylog("debug", f"[WF] Updating Device '{obj.get('devGUID')}'")
            DeviceInstance().updateField(obj["devGUID"], self.field, final_value)
            return obj

        mylog("none", f"[WF] UpdateFieldAction: unsupported object format: {obj}")
        return None

    def _archive_conflicting_mac(self, new_mac, current_guid):
        """If another device already holds *new_mac*, archive it before the
        primary-key mutation so SQLite's UNIQUE constraint is not violated."""
        normalized = normalize_mac(new_mac)
        existing = DeviceInstance().getByMac(normalized)
        if existing and existing.get("devGUID") != current_guid:
            mylog("none", [
                f"[WF] Archiving conflicting device {existing['devGUID']} "
                f"(MAC {normalized}) before devMac update"
            ])
            DeviceInstance().updateField(existing["devGUID"], "devIsArchived", 1)


class DeleteObjectAction(Action):
    """Action to delete a device or plugin object.

    When *target_device* is supplied the action deletes that device rather than
    the one that raised the event, enabling cross-device targeting (v2).
    """

    def __init__(self, db, trigger, target_device=None):
        super().__init__(trigger)
        self.db = db
        self.target_device = target_device

    def execute(self):
        obj = self.target_device if self.target_device is not None else self.get_object()

        if isinstance(obj, sqlite3.Row):
            obj = dict(obj)

        if obj is None:
            mylog("none", "[WF] DeleteObjectAction: target device no longer exists")
            return None

        mylog("verbose", f"[WF] Deleting device {obj.get('devGUID', obj.get('objectGuid', '?'))}")

        if "objectGuid" in obj:
            mylog("debug", f"[WF] Deleting Object '{obj}'")
            PluginObjectInstance().delete(obj["objectGuid"])
            return obj

        if "devGUID" in obj:
            mylog("debug", f"[WF] Deleting Device '{obj.get('devGUID')}'")
            DeviceInstance().delete(obj["devGUID"])
            return obj

        mylog("none", f"[WF] DeleteObjectAction: unsupported object format: {obj}")
        return None


class RunPluginAction(Action):
    """Action to run a specific plugin."""

    def __init__(self, db, plugin_name, params, trigger):
        super().__init__(trigger)
        self.db = db
        self.plugin_name = plugin_name
        self.params = params

    def execute(self):
        obj = self.get_object()

        if obj is None:
            mylog("none", "[WF] Object no longer exists")
            return None

        mylog("verbose", f"[WF] Executing plugin '{self.plugin_name}' with parameters {self.params} for object {obj}")

        # PluginManager.run(self.plugin_name, self.params)

        return obj


class SendNotificationAction(Action):
    """Action to send a notification."""

    def __init__(self, method, message, trigger):
        super().__init__(trigger)
        self.method = method
        self.message = message

    def execute(self):
        obj = self.get_object()

        if obj is None:
            mylog("none", "[WF] Object no longer exists")
            return None

        mylog("verbose", f"[WF] Sending notification via '{self.method}': {self.message} for object {obj}")

        # NotificationManager.send(self.method, self.message)

        return obj


class ActionGroup:
    """Handles multiple actions applied to an object."""

    def __init__(self, actions):
        self.actions = actions

    def execute(self):
        for action in self.actions:
            action.execute()