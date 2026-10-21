"""
Regression guard for server/app_state.py's updateState()/broadcast_state_update()
call - pluginsStates must reach the SSE broadcast payload, not just the
persisted app_state.json. The original broadcast_state_update() call never
passed pluginsStates, so front/js/ui_components.js's watchPluginState() waited
on an SSE event that could never arrive.
"""

import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

import app_state  # noqa: E402


class TestAppStateSSEBroadcast(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._patchers = [
            patch("app_state.apiPath", self._tmpdir + os.sep),
            patch("app_state.checkNewVersion", lambda *a, **k: False),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self):
        for p in self._patchers:
            p.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_update_state_broadcasts_plugins_states(self):
        with patch("app_state.broadcast_state_update") as mock_broadcast:
            app_state.updateState(
                pluginsStates={"INTRSPD": {"stateUpdated": "2026-09-14 12:00:00", "totalObjects": 1}}
            )

        mock_broadcast.assert_called_once()
        _, kwargs = mock_broadcast.call_args
        self.assertIn("pluginsStates", kwargs)
        self.assertEqual(kwargs["pluginsStates"]["INTRSPD"]["totalObjects"], 1)

    def test_plugins_states_persist_and_merge_across_calls(self):
        """updateState() merges into the existing pluginsStates dict rather
        than replacing it - a second plugin's update must not drop the
        first's entry, and each broadcast must carry the full merged dict."""
        with patch("app_state.broadcast_state_update") as mock_broadcast:
            app_state.updateState(pluginsStates={"PLUGINA": {"stateUpdated": "2026-09-14 12:00:00"}})
            app_state.updateState(pluginsStates={"PLUGINB": {"stateUpdated": "2026-09-14 12:00:05"}})

        self.assertEqual(mock_broadcast.call_count, 2)
        _, last_kwargs = mock_broadcast.call_args
        self.assertIn("PLUGINA", last_kwargs["pluginsStates"])
        self.assertIn("PLUGINB", last_kwargs["pluginsStates"])


if __name__ == "__main__":
    unittest.main()
