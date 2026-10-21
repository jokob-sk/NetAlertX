"""
Tests for _publisher_pushsafer/pushsafer.py - focused on the per-notification
timeout wiring (RUN_TIMEOUT divided across a queue via
plugin_helper.per_item_timeout, instead of reused unchanged per call).

Run from inside the NetAlertX container, or locally - NetAlertX-specific
modules are stubbed out automatically before the script is imported.

    pytest test/plugins/test_pushsafer.py -v
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
_stub("plugin_helper", Plugin_Objects=MagicMock, handleEmpty=lambda v: v, per_item_timeout=lambda run_timeout, count, floor=1: run_timeout)
_stub("logger", mylog=lambda *a: None, Logger=MagicMock)
_stub("helper", get_setting_value=lambda k: "", hide_string=lambda s: "***")
_stub("utils")
_stub("utils.datetime_utils", timeNowUTC=lambda: "2026-01-01 00:00:00")
_stub("models")
_stub("models.notification_instance", NotificationInstance=MagicMock)
_stub("database", DB=MagicMock)

if "requests" not in sys.modules:
    _req = types.ModuleType("requests")
    _req.post = MagicMock
    _req_exc = types.ModuleType("requests.exceptions")
    _req_exc.RequestException = type("RequestException", (Exception,), {})
    _req.exceptions = _req_exc
    sys.modules["requests"] = _req
    sys.modules["requests.exceptions"] = _req_exc
    _stubbed_module_names.extend(["requests", "requests.exceptions"])

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server", "plugins", "_publisher_pushsafer"))

import pushsafer  # noqa: E402

# Stops these fake entries from shadowing the real modules for other test
# files collected later in the same pytest session (pushsafer's own
# module-level `from x import y` bindings are already resolved by now).
for _name in _stubbed_module_names:
    sys.modules.pop(_name, None)


class TestSendTimeout:
    def test_uses_explicit_timeout_when_given(self):
        mock_response = MagicMock(status_code=200, text="ok")
        with patch("pushsafer.requests.post", return_value=mock_response) as mock_post:
            pushsafer.send("hello", timeout=3)
        assert mock_post.call_args.kwargs["timeout"] == 3

    def test_falls_back_to_setting_when_timeout_not_given(self):
        mock_response = MagicMock(status_code=200, text="ok")
        with patch("pushsafer.get_setting_value", return_value="10"), \
                patch("pushsafer.requests.post", return_value=mock_response) as mock_post:
            pushsafer.send("hello")
        assert mock_post.call_args.kwargs["timeout"] == 10
