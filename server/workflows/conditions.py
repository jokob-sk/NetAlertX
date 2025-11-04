import re
import json
import os
import sys

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog, Logger
from helper import get_setting_value

# Make sure log level is initialized correctly
Logger(get_setting_value("LOG_LEVEL"))


class Condition:
    """Evaluates a single condition."""

    def __init__(self, condition_json):
        self.field = condition_json["field"]
        self.operator = condition_json["operator"]
        self.value = condition_json["value"]
        self.negate = condition_json.get("negate", False)

    def evaluate(self, trigger):
        # try finding the value of the field on the event triggering this workflow or thre object triggering the app event
        appEvent_value = (
            trigger.event[self.field] if self.field in trigger.event.keys() else None
        )
        eveObj_value = (
            trigger.object[self.field] if self.field in trigger.object.keys() else None
        )

        # proceed only if value found
        if appEvent_value is None and eveObj_value is None:
            return False
        elif appEvent_value is not None:
            obj_value = appEvent_value
        elif eveObj_value is not None:
            obj_value = eveObj_value

        # process based on operators
        if self.operator == "equals":
            result = str(obj_value) == str(self.value)
        elif self.operator == "contains":
            result = str(self.value).lower() in str(obj_value).lower()
        elif self.operator == "regex":
            result = bool(re.match(self.value, str(obj_value)))
        else:
            m = f"[WF] Unsupported operator: {self.operator}"
            mylog("none", [m])
            raise ValueError(m)

        return not result if self.negate else result


class ConditionGroup:
    """Handles condition groups with AND, OR logic, supporting nested groups."""

    def __init__(self, group_json):
        mylog(
            "verbose",
            [f"[WF] ConditionGroup json.dumps(group_json): {json.dumps(group_json)}"],
        )

        self.logic = group_json.get("logic", "AND").upper()
        self.conditions = []

        for condition in group_json["conditions"]:
            if "field" in condition:  # Simple condition
                self.conditions.append(Condition(condition))
            else:  # Nested condition group
                self.conditions.append(ConditionGroup(condition))

    def evaluate(self, event):
        results = [condition.evaluate(event) for condition in self.conditions]

        if self.logic == "AND":
            return all(results)
        elif self.logic == "OR":
            return any(results)
        else:
            m = f"[WF] ConditionGroup unsupported logic: {self.logic}"
            mylog("verbose", [m])
            raise ValueError(m)
