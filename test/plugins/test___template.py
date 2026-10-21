"""
Tests for the __template plugin scaffold (server/plugins/__template/rename_me.py).

This is the copy-paste starting point for every new plugin, so keeping it
covered by a passing test (and demonstrating the expected test shape) gives
new plugin authors something to copy alongside the script itself.

Run from inside the NetAlertX container, or locally - NetAlertX-specific
modules are stubbed out automatically before the script is imported.

    pytest "test/plugins/test___template.py" -v
"""

import base64
import json
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch

_tmp_log = tempfile.mkdtemp()
_tmp_db = tempfile.mkdtemp()


def _decode_settings_base64(encoded_str, convert_types=True):
    """Mirrors plugin_helper.decode_settings_base64 - reimplemented here
    (rather than importing the real plugin_helper.py) since that module's
    other top-level imports need the full container environment."""
    settings_list = json.loads(base64.b64decode(encoded_str).decode("utf-8"))
    result = {}
    for _, key, _type, value in settings_list:
        result[key] = value.lower() == "true" if convert_types and _type.lower() == "boolean" else value
    return result


def _encode_instance(name, url, enabled):
    payload = [
        ["group", "TMP_instance_name", "string", name],
        ["group", "TMP_instance_url", "string", url],
        ["group", "TMP_instance_enabled", "boolean", str(enabled)],
    ]
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")

_stubbed_module_names = []


def _stub(name: str, **attrs):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[name] = mod
        _stubbed_module_names.append(name)


_stub("pytz", timezone=lambda tz: tz)
_stub("conf")
_stub("const", dataPath=_tmp_db, dbFolderPath=_tmp_db, configPath=_tmp_db, logPath=_tmp_log)
_stub("plugin_helper", Plugin_Objects=MagicMock, decode_settings_base64=_decode_settings_base64)
_stub("logger", mylog=lambda *a: None, Logger=MagicMock)
_stub("helper", get_setting_value=lambda k: "")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server", "plugins", "__template"))

import rename_me  # noqa: E402

# Stops these fake entries from shadowing the real modules for other test
# files collected later in the same pytest session (rename_me's own
# module-level `from x import y` bindings are already resolved by now).
for _name in _stubbed_module_names:
    sys.modules.pop(_name, None)


class TestGetDeviceData:
    def test_returns_the_sample_devices(self):
        data = rename_me.get_device_data(some_setting="anything")
        assert len(data) == 2
        assert {d["mac_address"] for d in data} == {"00:11:22:33:44:55", "00:11:22:33:44:66"}
        for device in data:
            for key in ("mac_address", "ip_address", "hostname", "vendor", "device_type", "last_seen"):
                assert key in device


class TestGetConfiguredInstances:
    def test_decodes_and_returns_enabled_instances(self):
        raw = [
            _encode_instance("Site A", "https://a.example", True),
            _encode_instance("Site B", "https://b.example", False),
        ]
        with patch("rename_me.get_setting_value", side_effect=lambda k: raw if k == "TMP_nested_form_example" else ""):
            instances = rename_me.get_configured_instances()

        assert instances == [{"name": "Site A", "url": "https://a.example", "enabled": True}]

    def test_empty_setting_returns_no_instances(self):
        with patch("rename_me.get_setting_value", return_value=""):
            assert rename_me.get_configured_instances() == []


class TestMain:
    def test_writes_one_object_per_device_and_result_file_once(self):
        rename_me.plugin_objects = MagicMock()
        rename_me.plugin_objects.__len__ = lambda self: 2

        rename_me.main()

        assert rename_me.plugin_objects.add_object.call_count == 2
        rename_me.plugin_objects.write_result_file.assert_called_once()
