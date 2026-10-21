"""
Tests for _publisher_telegram/tg.py - focused on the per-notification timeout
wiring (RUN_TIMEOUT divided across a queue via plugin_helper.per_item_timeout,
instead of reused unchanged per call).

Run from inside the NetAlertX container, or locally - NetAlertX-specific
modules are stubbed out automatically before the script is imported.

    pytest test/plugins/test_tg.py -v
"""

import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch

_tmp_log = tempfile.mkdtemp()

_stubbed_module_names = []


def _stub(name: str, **attrs):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[name] = mod
        _stubbed_module_names.append(name)


_stub("pytz", timezone=lambda tz: tz)
_stub("conf", tz=None)
_stub("const", confFileName="app.conf", logPath=_tmp_log)
_stub("plugin_helper", Plugin_Objects=MagicMock, per_item_timeout=lambda run_timeout, count, floor=1: run_timeout)
_stub("logger", mylog=lambda *a: None, Logger=MagicMock)
_stub("helper", get_setting_value=lambda k: "")
_stub("utils")
_stub("utils.datetime_utils", timeNowUTC=lambda: "2026-01-01 00:00:00")
_stub("models")
_stub("models.notification_instance", NotificationInstance=MagicMock)
_stub("database", DB=MagicMock)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server", "plugins", "_publisher_telegram"))

import tg  # noqa: E402

# Stops these fake entries from shadowing the real modules for other test
# files collected later in the same pytest session (tg's own module-level
# `from x import y` bindings are already resolved by now).
for _name in _stubbed_module_names:
    sys.modules.pop(_name, None)


def _mock_proc(stdout='{"ok": true}'):
    return MagicMock(stdout=stdout, returncode=0)


def _settings(run_timeout="10", size=4096, host="123:ABC", url="123:ABC"):
    values = {
        "TELEGRAM_SIZE": size,
        "TELEGRAM_RUN_TIMEOUT": run_timeout,
        "TELEGRAM_HOST": host,
        "TELEGRAM_URL": url,
    }
    return lambda key: values.get(key, "")


class TestSendTimeout:
    def test_uses_explicit_timeout_for_curl(self):
        with patch("tg.get_setting_value", side_effect=_settings(run_timeout="1000")), \
                patch("tg.subprocess.run", return_value=_mock_proc()) as mock_run:
            tg.send("hello", timeout=5)
        cmd = mock_run.call_args.args[0]
        assert cmd[cmd.index("--connect-timeout") + 1] == "4"  # timeout - 1
        assert cmd[cmd.index("--max-time") + 1] == "4"

    def test_falls_back_to_setting_when_timeout_not_given(self):
        with patch("tg.get_setting_value", side_effect=_settings(run_timeout="10")), \
                patch("tg.subprocess.run", return_value=_mock_proc()) as mock_run:
            tg.send("hello")
        cmd = mock_run.call_args.args[0]
        assert cmd[cmd.index("--connect-timeout") + 1] == "9"  # setting(10) - 1

    def test_curl_timeout_floor_is_one(self):
        with patch("tg.get_setting_value", side_effect=_settings()), \
                patch("tg.subprocess.run", return_value=_mock_proc()) as mock_run:
            tg.send("hello", timeout=1)
        cmd = mock_run.call_args.args[0]
        assert cmd[cmd.index("--connect-timeout") + 1] == "1"  # max(1, 1-1)
