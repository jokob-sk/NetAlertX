"""
Unit tests for Workflow Engine v2 — cross-device targeting.

Covers:
  - interpolate_tokens()
  - WorkflowManager.VALID_DEVICE_COLUMNS token validation
  - WorkflowManager._validate_workflow_tokens()
  - WorkflowManager.load_workflows() rejects invalid-token workflows
  - DeviceInstance.queryByConditions()
  - UpdateFieldAction boolean column casting
  - UpdateFieldAction _archive_conflicting_mac guard
  - WorkflowManager._mutated_guids cascade prevention
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db_test_helpers import (
    make_db, make_device_dict, insert_device_from_dict,
    CREATE_PLUGINS_OBJECTS, CREATE_PLUGINS_HISTORY,
)


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------

def _make_app_event(guid="evt-guid-1", obj_guid="dev-guid-1", obj_type="Devices",
                    event_type="update", index=1):
    """Return a dict mimicking an AppEvents sqlite3.Row."""
    return {
        "guid": guid,
        "objectGuid": obj_guid,
        "objectType": obj_type,
        "appEventType": event_type,
        "appEventProcessed": 0,
        "index": index,
    }


def make_stub_manager():
    """Return a WorkflowManager with a mock DB and no workflows loaded."""
    from workflows.manager import WorkflowManager
    db = MagicMock()
    db.sql = MagicMock()
    db.sql.execute.return_value.fetchall.return_value = []
    db.commitDB = MagicMock()
    with patch.object(WorkflowManager, "load_workflows", return_value=[]):
        mgr = WorkflowManager(db)
    return mgr


# ---------------------------------------------------------------------------
# interpolate_tokens
# ---------------------------------------------------------------------------

class TestInterpolateTokens(unittest.TestCase):

    def setUp(self):
        from workflows.actions import interpolate_tokens
        self.interpolate = interpolate_tokens

    def test_replaces_known_token(self):
        device = {"devLastIP": "10.0.0.5", "devMac": "aa:bb:cc:dd:ee:ff"}
        result = self.interpolate("{{trigger.devLastIP}}", device)
        self.assertEqual(result, "10.0.0.5")

    def test_replaces_multiple_tokens(self):
        device = {"devLastIP": "10.0.0.5", "devMac": "aa:bb:cc:dd:ee:ff"}
        result = self.interpolate("ip={{trigger.devLastIP}} mac={{trigger.devMac}}", device)
        self.assertEqual(result, "ip=10.0.0.5 mac=aa:bb:cc:dd:ee:ff")

    def test_leaves_unknown_token_unchanged(self):
        device = {"devLastIP": "10.0.0.5"}
        result = self.interpolate("{{trigger.doesNotExist}}", device)
        self.assertEqual(result, "{{trigger.doesNotExist}}")

    def test_non_string_value_returned_as_is(self):
        device = {}
        self.assertEqual(self.interpolate(42, device), 42)
        self.assertIsNone(self.interpolate(None, device))

    def test_empty_device_dict_leaves_token_unchanged(self):
        result = self.interpolate("{{trigger.devMac}}", {})
        self.assertEqual(result, "{{trigger.devMac}}")


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------

class TestValidateWorkflowTokens(unittest.TestCase):

    def test_valid_token_passes(self):
        mgr = make_stub_manager()
        wf = {"name": "test", "actions": [{"value": "{{trigger.devLastIP}}"}]}
        self.assertTrue(mgr._validate_workflow_tokens(wf))

    def test_invalid_token_fails(self):
        mgr = make_stub_manager()
        wf = {"name": "test", "actions": [{"value": "{{trigger.ip_address}}"}]}
        self.assertFalse(mgr._validate_workflow_tokens(wf))

    def test_nested_invalid_token_fails(self):
        mgr = make_stub_manager()
        wf = {
            "name": "test",
            "actions": [{
                "target": {
                    "conditions": [{"value": "{{trigger.bad_field}}"}]
                }
            }]
        }
        self.assertFalse(mgr._validate_workflow_tokens(wf))

    def test_no_tokens_passes(self):
        mgr = make_stub_manager()
        wf = {"name": "test", "conditions": [], "actions": [{"value": "static"}]}
        self.assertTrue(mgr._validate_workflow_tokens(wf))


class TestLoadWorkflowsRejectsInvalidTokens(unittest.TestCase):

    def _make_manager_loading(self, raw_workflows):
        """Build a WorkflowManager whose load_workflows() reads from a temp file."""
        import workflows.manager as wf_mod
        from workflows.manager import WorkflowManager

        with tempfile.TemporaryDirectory() as tmpdir:
            wf_path = os.path.join(tmpdir, "workflows.json")
            with open(wf_path, "w") as f:
                json.dump(raw_workflows, f)

            orig = wf_mod.fullConfFolder
            wf_mod.fullConfFolder = tmpdir
            try:
                db = MagicMock()
                with patch.object(WorkflowManager, "load_workflows", return_value=[]):
                    mgr = WorkflowManager(db)
                mgr.workflows = mgr.load_workflows()
            finally:
                wf_mod.fullConfFolder = orig
        return mgr

    def test_valid_workflow_loaded(self):
        wf = {
            "name": "Valid WF", "enabled": "Yes",
            "trigger": {"object_type": "Devices", "event_type": "update"},
            "conditions": [],
            "actions": [{"type": "update_field", "field": "devIsNew",
                          "value": "{{trigger.devLastIP}}"}]
        }
        mgr = self._make_manager_loading([wf])
        self.assertEqual(len(mgr.workflows), 1)

    def test_invalid_token_workflow_rejected(self):
        wf = {
            "name": "Bad WF", "enabled": "Yes",
            "trigger": {"object_type": "Devices", "event_type": "update"},
            "conditions": [],
            "actions": [{"type": "update_field", "field": "devIsNew",
                          "value": "{{trigger.nonexistent_field}}"}]
        }
        mgr = self._make_manager_loading([wf])
        self.assertEqual(len(mgr.workflows), 0)


# ---------------------------------------------------------------------------
# DeviceInstance.queryByConditions
# ---------------------------------------------------------------------------

class TestQueryByConditions(unittest.TestCase):

    def setUp(self):
        self.conn = make_db()
        dev_a = make_device_dict("aa:bb:cc:dd:ee:01", devLastIP="192.168.1.10",
                                  devGUID="guid-a", devIsArchived=0)
        dev_b = make_device_dict("aa:bb:cc:dd:ee:02", devLastIP="192.168.1.10",
                                  devGUID="guid-b", devIsArchived=0)
        dev_c = make_device_dict("aa:bb:cc:dd:ee:03", devLastIP="192.168.1.20",
                                  devGUID="guid-c", devIsArchived=0)
        for d in [dev_a, dev_b, dev_c]:
            insert_device_from_dict(self.conn, d)

    def _instance(self):
        from models.device_instance import DeviceInstance
        inst = DeviceInstance()
        # Patch _fetchall to use our in-memory connection
        def _fetchall(q, p=()):
            rows = self.conn.execute(q, p).fetchall()
            return [dict(r) for r in rows]
        inst._fetchall = _fetchall
        return inst

    def test_equals_returns_matching_devices(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "equals", "value": "192.168.1.10"}
        ])
        macs = {r["devMac"] for r in results}
        self.assertIn("aa:bb:cc:dd:ee:01", macs)
        self.assertIn("aa:bb:cc:dd:ee:02", macs)
        self.assertNotIn("aa:bb:cc:dd:ee:03", macs)

    def test_multiple_conditions_and_logic(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "equals", "value": "192.168.1.10"},
            {"field": "devMac", "operator": "equals", "value": "aa:bb:cc:dd:ee:01"},
        ])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["devMac"], "aa:bb:cc:dd:ee:01")

    def test_contains_operator(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "contains", "value": "192.168.1"}
        ])
        self.assertEqual(len(results), 3)

    def test_empty_conditions_returns_empty(self):
        inst = self._instance()
        results = inst.queryByConditions([])
        self.assertEqual(results, [])

    def test_unknown_field_skipped_returns_empty(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "nonexistent_column", "operator": "equals", "value": "x"}
        ])
        self.assertEqual(results, [])

    def test_unknown_operator_skipped_returns_empty(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "regex", "value": ".*"}
        ])
        self.assertEqual(results, [])

    def test_not_equals_operator(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "not_equals", "value": "192.168.1.10"}
        ])
        macs = {r["devMac"] for r in results}
        self.assertNotIn("aa:bb:cc:dd:ee:01", macs)
        self.assertNotIn("aa:bb:cc:dd:ee:02", macs)
        self.assertIn("aa:bb:cc:dd:ee:03", macs)

    def test_not_contains_operator(self):
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "not_contains", "value": "192.168.1.1"}
        ])
        macs = {r["devMac"] for r in results}
        # .10 contains "192.168.1.1", .20 does not
        self.assertNotIn("aa:bb:cc:dd:ee:01", macs)
        self.assertNotIn("aa:bb:cc:dd:ee:02", macs)
        self.assertIn("aa:bb:cc:dd:ee:03", macs)

    def test_not_equals_combined_with_equals(self):
        """Exclude trigger device by MAC while matching on IP — the core use case."""
        inst = self._instance()
        results = inst.queryByConditions([
            {"field": "devLastIP", "operator": "equals", "value": "192.168.1.10"},
            {"field": "devMac", "operator": "not_equals", "value": "aa:bb:cc:dd:ee:01"},
        ])
        macs = {r["devMac"] for r in results}
        self.assertNotIn("aa:bb:cc:dd:ee:01", macs)
        self.assertIn("aa:bb:cc:dd:ee:02", macs)
        self.assertNotIn("aa:bb:cc:dd:ee:03", macs)


# ---------------------------------------------------------------------------
# UpdateFieldAction — boolean cast
# ---------------------------------------------------------------------------

class TestUpdateFieldActionBooleanCast(unittest.TestCase):

    def setUp(self):
        self.conn = make_db()
        dev = make_device_dict("aa:bb:cc:dd:ee:ff", devGUID="guid-1", devIsArchived=0)
        insert_device_from_dict(self.conn, dev)

    def _make_action(self, field, value, target_device):
        from workflows.actions import UpdateFieldAction
        trigger = MagicMock()
        trigger.object = None
        trigger.object_type = "Devices"
        db = MagicMock()

        action = UpdateFieldAction(db, field, value, trigger, target_device)

        # Patch DeviceInstance.updateField to capture what value is written
        self.written_value = None
        def fake_update(guid, f, v):
            self.written_value = v
        with patch("workflows.actions.DeviceInstance") as MockDI:
            MockDI.return_value.updateField.side_effect = fake_update
            action.execute()

        return self.written_value

    def test_string_one_cast_to_int_for_boolean_column(self):
        target = {"devGUID": "guid-1", "devIsArchived": 0}
        written = self._make_action("devIsArchived", "1", target)
        self.assertEqual(written, 1)
        self.assertIsInstance(written, int)

    def test_string_zero_cast_to_int_for_boolean_column(self):
        target = {"devGUID": "guid-1", "devIsArchived": 1}
        written = self._make_action("devIsArchived", "0", target)
        self.assertEqual(written, 0)
        self.assertIsInstance(written, int)

    def test_non_boolean_column_not_cast(self):
        target = {"devGUID": "guid-1", "devName": "OldName"}
        written = self._make_action("devName", "NewName", target)
        self.assertEqual(written, "NewName")
        self.assertIsInstance(written, str)

    def test_invalid_boolean_value_skips_update(self):
        target = {"devGUID": "guid-1", "devIsArchived": 0}
        written = self._make_action("devIsArchived", "not_an_int", target)
        self.assertIsNone(written)


# ---------------------------------------------------------------------------
# UpdateFieldAction — devMac conflict archive guard
# ---------------------------------------------------------------------------

class TestUpdateFieldActionMacGuard(unittest.TestCase):

    def test_conflicting_mac_device_archived(self):
        from workflows.actions import UpdateFieldAction
        trigger = MagicMock()
        trigger.object = None
        db = MagicMock()

        conflicting = {"devGUID": "guid-conflict", "devMac": "aa:bb:cc:dd:ee:ff"}
        current_guid = "guid-current"
        target_device = {"devGUID": current_guid, "devMac": "11:22:33:44:55:66"}

        action = UpdateFieldAction(db, "devMac", "aa:bb:cc:dd:ee:ff", trigger, target_device)

        archived_guid = None
        def fake_update(guid, field, value):
            nonlocal archived_guid
            if field == "devIsArchived":
                archived_guid = guid

        with patch("workflows.actions.DeviceInstance") as MockDI:
            MockDI.return_value.getByMac.return_value = conflicting
            MockDI.return_value.updateField.side_effect = fake_update
            action.execute()

        self.assertEqual(archived_guid, "guid-conflict")

    def test_no_conflicting_mac_no_archive(self):
        from workflows.actions import UpdateFieldAction
        trigger = MagicMock()
        trigger.object = None
        db = MagicMock()

        target_device = {"devGUID": "guid-current", "devMac": "11:22:33:44:55:66"}
        action = UpdateFieldAction(db, "devMac", "aa:bb:cc:dd:ee:ff", trigger, target_device)

        archived_guid = None
        def fake_update(guid, field, value):
            nonlocal archived_guid
            if field == "devIsArchived":
                archived_guid = guid

        with patch("workflows.actions.DeviceInstance") as MockDI:
            MockDI.return_value.getByMac.return_value = None
            MockDI.return_value.updateField.side_effect = fake_update
            action.execute()

        self.assertIsNone(archived_guid)


# ---------------------------------------------------------------------------
# Cascade prevention — _mutated_guids
# ---------------------------------------------------------------------------

class TestCascadePrevention(unittest.TestCase):

    def test_mutated_guid_blocks_event(self):
        mgr = make_stub_manager()
        mgr._mutated_guids.add("dev-guid-42")

        event = _make_app_event(guid="evt-1", obj_guid="dev-guid-42")
        # Make event dict-accessible
        event = MagicMock()
        event.__getitem__ = lambda s, k: {"guid": "evt-1", "objectGuid": "dev-guid-42",
                                           "index": 1}[k]

        # process_event should skip without calling execute_workflow
        with patch.object(mgr, "execute_workflow") as mock_exec:
            mgr.process_event(event)
            mock_exec.assert_not_called()

    def test_get_new_app_events_clears_mutated_guids(self):
        mgr = make_stub_manager()
        mgr._mutated_guids.add("some-guid")

        mgr.db.sql.execute.return_value.fetchall.return_value = []
        mgr.get_new_app_events()

        self.assertEqual(len(mgr._mutated_guids), 0)

    def test_execute_actions_adds_to_mutated_guids(self):
        mgr = make_stub_manager()

        target_device = {"devGUID": "guid-mutated", "devIsArchived": 0}

        actions = [{"type": "update_field", "field": "devIsArchived", "value": "1"}]

        trigger = MagicMock()
        trigger.object = None

        with patch("workflows.manager.DeviceInstance"), \
             patch("workflows.actions.DeviceInstance") as MockDI:
            MockDI.return_value.updateField = MagicMock()
            with patch.object(mgr, "_resolve_target_devices", return_value=[target_device]):
                mgr.execute_actions(actions, trigger)

        self.assertIn("guid-mutated", mgr._mutated_guids)


class TestConditionHandlesMissingTriggerObject(unittest.TestCase):
    """Regression test: trigger.object is None whenever the AppEvent's
    objectGuid no longer matches any Devices/Plugins_Objects row by the time
    the event is processed (e.g. the device was deleted between AppEvent
    creation and workflow processing - see workflows/triggers.py's own None
    branches). Condition.evaluate() must not crash on it."""

    def _make_trigger(self, event, obj=None):
        from types import SimpleNamespace
        return SimpleNamespace(event=event, object=obj)

    def test_condition_on_missing_field_returns_false_not_crash(self):
        from workflows.conditions import Condition

        event = _make_app_event()
        trigger = self._make_trigger(event, obj=None)

        condition = Condition({"field": "devLocation", "operator": "equals", "value": "Office"})
        # must not raise AttributeError: 'NoneType' object has no attribute 'keys'
        self.assertFalse(condition.evaluate(trigger))

    def test_condition_on_event_field_still_works_when_object_missing(self):
        """A field present on the AppEvent itself must still evaluate correctly
        even when trigger.object is None."""
        from workflows.conditions import Condition

        event = _make_app_event(event_type="update")
        trigger = self._make_trigger(event, obj=None)

        condition = Condition({"field": "appEventType", "operator": "equals", "value": "update"})
        self.assertTrue(condition.evaluate(trigger))


class TestTriggerDeviceGuidLookup(unittest.TestCase):
    """Trigger.__init__'s Devices/devGUID lookup (workflows/triggers.py) -
    covers the parameterized query and the idx_dev_guid index added
    alongside it."""

    def setUp(self):
        from types import SimpleNamespace
        self.conn = make_db()
        self.db = SimpleNamespace(sql=self.conn)
        dev = make_device_dict("aa:bb:cc:dd:ee:01", devGUID="guid-a")
        insert_device_from_dict(self.conn, dev)

    def test_lookup_finds_matching_device(self):
        from workflows.triggers import Trigger

        event = _make_app_event(obj_guid="guid-a", obj_type="Devices", event_type="update")
        trigger = Trigger({"object_type": "Devices", "event_type": "update"}, event, self.db)

        self.assertIsNotNone(trigger.object)
        self.assertEqual(trigger.object["devMac"], "aa:bb:cc:dd:ee:01")

    def test_query_is_parameterized_not_string_interpolated(self):
        """A devGUID containing a single quote must not raise
        sqlite3.OperationalError - regression guard against reverting to
        f-string interpolation of event['objectGuid']."""
        from workflows.triggers import Trigger

        event = _make_app_event(obj_guid="a'b", obj_type="Devices", event_type="update")
        trigger = Trigger({"object_type": "Devices", "event_type": "update"}, event, self.db)

        self.assertIsNone(trigger.object)

    def test_devguid_lookup_uses_index(self):
        from db.db_upgrade import ensure_Indexes

        # ensure_Indexes() also indexes Plugins_Objects.objectGuid and
        # Plugins_History(plugin, dateTimeChanged), neither of which
        # make_db()'s minimal fixture creates.
        self.conn.execute(CREATE_PLUGINS_OBJECTS)
        self.conn.execute(CREATE_PLUGINS_HISTORY)
        ensure_Indexes(self.conn)

        plan = self.conn.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM Devices WHERE devGUID = ?", ("guid-a",)
        ).fetchall()
        plan_text = " ".join(str(tuple(row)) for row in plan)

        self.assertIn("idx_dev_guid", plan_text)
        self.assertNotIn("SCAN Devices", plan_text)


if __name__ == "__main__":
    unittest.main()
