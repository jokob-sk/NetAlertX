"""
Unit tests for the execution_queue.log action-string format and dispatch
(server/models/user_events_queue_instance.py, plugin.check_and_run_user_event()).

Covers the fix for updateApi() (front/js/common.js) prepending an extra
client-side GUID onto its action string, which broke check_and_run_user_event()
and finalize_event()'s shared "split('|')[2:4]" parsing - see
.gemini/internal-docs/PRDs/execution-queue-fe-locking-fix.md, fix A.
"""

import os
import sys
import tempfile
import shutil
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from models.user_events_queue_instance import UserEventsQueueInstance  # noqa: E402
import plugin as plugin_module  # noqa: E402


class TestExecutionQueueDispatch(unittest.TestCase):
    """Isolates execution_queue.log to a temp dir so tests don't touch the
    real logPath, and don't depend on plugin_manager's full __init__ (DB
    settings cache, schedules, logger) - check_and_run_user_event() only
    touches self.db/self.all_plugins, so a bare SimpleNamespace stands in."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._patcher = patch("models.user_events_queue_instance.logPath", self._tmpdir)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _fake_manager(self):
        return SimpleNamespace(db=None, all_plugins=[])

    def test_check_and_run_user_event_dispatches_update_api(self):
        """The fixed action format (no extra client GUID) must reach the
        elif event == "update_api" branch and call update_api() with the
        parsed params and is_ad_hoc_user_event=True. finalize_event("update_api")
        is called inside the real update_api()'s try_write() (api.py:205-208),
        not here - since update_api is mocked, the line is expected to still
        be in the log (verified separately in test_finalize_event_removes_update_api_line)."""
        q = UserEventsQueueInstance()
        q.add_event("update_api|devices,appevents")

        with patch("plugin.update_api") as mock_update_api:
            plugin_module.plugin_manager.check_and_run_user_event(self._fake_manager())

        mock_update_api.assert_called_once_with(None, [], False, ["devices", "appevents"], True)

    def test_finalize_event_removes_update_api_line(self):
        q = UserEventsQueueInstance()
        q.add_event("update_api|devices,appevents")

        removed = q.finalize_event("update_api")

        self.assertTrue(removed)
        self.assertEqual(q.read_log(), [])

    def test_malformed_action_falls_through_to_unhandled_branch(self):
        """Regression guard for the exact bug fixed: an action string with an
        extra field before "update_api" (the old updateApi() format) must
        NOT reach the update_api() call - it's misrouted into the "else"
        unhandled-event branch instead. The line still gets removed (both
        check_and_run_user_event() and finalize_event() parse it the same
        wrong way and agree with each other), but the intended fast-refresh
        never fires."""
        q = UserEventsQueueInstance()
        q.add_event("11111111-1111-1111-1111-111111111111|update_api|devices,appevents")

        with patch("plugin.update_api") as mock_update_api:
            plugin_module.plugin_manager.check_and_run_user_event(self._fake_manager())

        mock_update_api.assert_not_called()
        self.assertEqual(q.read_log(), [])


if __name__ == "__main__":
    unittest.main()
