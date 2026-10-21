"""
Tests for _publisher_ntfy/ntfy.py custom header parsing.

Run from inside the NetAlertX container (where the full environment is available),
or locally — in that case the NetAlertX-specific modules are stubbed out
automatically before the script is imported.

    pytest test/plugins/test_ntfy_custom_headers.py -v
"""

import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub NetAlertX-specific modules so tests can run outside the container.
# These stubs are only placeholders for the duration of the `import ntfy`
# below - they are popped from sys.modules again right after, so they don't
# leak into other test files sharing the same pytest session (which would
# otherwise shadow the real modules, e.g. models.notification_instance, for
# every subsequent test).
# ---------------------------------------------------------------------------
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
_stub("utils")
_stub("utils.datetime_utils", timeNowUTC=lambda: "2026-01-01 00:00:00")
_stub("logger", mylog=lambda *a: None, Logger=MagicMock)
_stub("helper", get_setting_value=lambda k, default="": "")
_stub("models")
_stub("models.notification_instance", NotificationInstance=MagicMock)
_stub("database", DB=MagicMock)

if "requests" not in sys.modules:
    _req = types.ModuleType("requests")
    _req.post = MagicMock
    _req_exc = types.ModuleType("requests.exceptions")
    _req_exc.InvalidHeader = type("InvalidHeader", (Exception,), {})
    _req_exc.RequestException = type("RequestException", (Exception,), {})
    _req.exceptions = _req_exc
    sys.modules["requests"] = _req
    sys.modules["requests.exceptions"] = _req_exc
    _stubbed_module_names.extend(["requests", "requests.exceptions"])

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server", "plugins", "_publisher_ntfy"))

import ntfy  # noqa: E402
from ntfy import build_custom_headers  # noqa: E402

# `ntfy` has already resolved its module-level `from x import y` bindings at
# this point, so removing these fake entries from sys.modules doesn't affect
# it - it just stops them from shadowing the real modules for other test
# files collected later in the same pytest session.
for _name in _stubbed_module_names:
    sys.modules.pop(_name, None)

BUILT_IN = {"Title": "NetAlertX Notification", "Authorization": "Bearer secret"}


def test_parses_a_single_header():
    assert build_custom_headers(["X-Token: abc123"], {}) == {"X-Token": "abc123"}


def test_parses_multiple_headers():
    entries = ["P-Access-Token-Id: id123", "P-Access-Token: token456"]

    assert build_custom_headers(entries, {}) == {
        "P-Access-Token-Id": "id123",
        "P-Access-Token": "token456",
    }


def test_trims_surrounding_whitespace():
    assert build_custom_headers(["  X-Token :  abc123  "], {}) == {"X-Token": "abc123"}


def test_keeps_colons_inside_the_value():
    assert build_custom_headers(["X-Token: id:secret"], {}) == {"X-Token": "id:secret"}


def test_skips_entries_without_a_separator():
    assert build_custom_headers(["X-Token abc123"], {}) == {}


def test_skips_entries_missing_a_name_or_value():
    assert build_custom_headers([": abc123", "X-Token:", "", "   "], {}) == {}


def test_skips_names_that_collide_with_a_built_in_header():
    assert build_custom_headers(["Authorization: Bearer mine"], BUILT_IN) == {}


def test_collision_check_ignores_case():
    assert build_custom_headers(["authorization: Bearer mine"], BUILT_IN) == {}


def test_keeps_the_first_of_a_repeated_name():
    assert build_custom_headers(["X-Token: first", "X-Token: second"], {}) == {"X-Token": "first"}


def test_a_bad_entry_does_not_discard_the_good_ones():
    entries = ["Authorization: Bearer mine", "malformed", "P-Access-Token: token456"]

    assert build_custom_headers(entries, BUILT_IN) == {"P-Access-Token": "token456"}


def test_no_entries_produces_no_headers():
    assert build_custom_headers([], BUILT_IN) == {}


def test_skips_values_containing_a_newline():
    assert build_custom_headers(["X-Token: abc\ndef"], {}) == {}


def test_skips_values_containing_a_carriage_return():
    assert build_custom_headers(["X-Token: abc\r\nInjected: 1"], {}) == {}


def test_skips_non_ascii_names_and_values():
    assert build_custom_headers(["X-Token: caf\u00e9", "X-T\u00e9st: abc"], {}) == {}


def test_an_unsendable_entry_does_not_discard_the_good_ones():
    entries = ["X-Bad: abc\ndef", "P-Access-Token: token456"]

    assert build_custom_headers(entries, {}) == {"P-Access-Token": "token456"}


SEND_SETTINGS = {
    "NTFY_HOST": "https://ntfy.example.com",
    "NTFY_TOPIC": "netalertx",
    "NTFY_TOKEN": "tk_secret",
    "NTFY_USER": "",
    "NTFY_PASSWORD": "",
    "NTFY_VERIFY_SSL": True,
    "NTFY_URL_QUERY_STRING": "",
    "NTFY_PRIORITY": "default",
    "NTFY_RUN_TIMEOUT": 10,
    "REPORT_DASHBOARD_URL": "http://localhost:20211",
}


def send_with(custom_headers):
    settings = dict(SEND_SETTINGS, NTFY_CUSTOM_HEADERS=custom_headers)
    response = MagicMock(status_code=200, text="ok")

    with patch.object(ntfy, "get_setting_value", lambda key: settings[key]), \
            patch.object(ntfy.requests, "post", return_value=response) as post:
        ntfy.send("<b>html</b>", "text")

    return post.call_args.kwargs["headers"]


def test_send_passes_accepted_custom_headers_to_requests():
    headers = send_with(["P-Access-Token-Id: id123", "P-Access-Token: token456"])

    assert headers["P-Access-Token-Id"] == "id123"
    assert headers["P-Access-Token"] == "token456"


def test_send_keeps_plugin_managed_headers_intact():
    headers = send_with(["Authorization: Bearer mine", "P-Access-Token: token456"])

    assert headers["Authorization"] == "Bearer tk_secret"
    assert headers["Title"] == "NetAlertX Notification"
    assert headers["P-Access-Token"] == "token456"


def test_send_drops_an_unsendable_custom_header_but_still_posts():
    headers = send_with(["X-Bad: abc\ndef", "P-Access-Token: token456"])

    assert "X-Bad" not in headers
    assert headers["P-Access-Token"] == "token456"
