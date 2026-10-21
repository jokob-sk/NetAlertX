"""Tests for the MikroTik DHCP lease scanner."""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_mikrotik_module():
    missing_module = object()
    previous_modules = {}

    def stub(name, **attributes):
        previous_modules[name] = sys.modules.get(name, missing_module)
        module = types.ModuleType(name)
        for attribute, value in attributes.items():
            setattr(module, attribute, value)
        sys.modules[name] = module

    class TrapError(Exception):
        pass

    stub(
        "plugin_helper",
        Plugin_Objects=MagicMock,
        normalize_mac=lambda mac: mac.strip().lower().replace("-", ":"),
    )
    stub("logger", mylog=MagicMock(), Logger=MagicMock())
    stub("helper", get_setting_value=MagicMock(return_value="UTC"))
    stub("const", logPath="/tmp")
    stub("conf", tz=None)
    stub("pytz", timezone=MagicMock(return_value="UTC"))
    stub("librouteros", connect=MagicMock())
    stub("librouteros.exceptions", TrapError=TrapError)

    module_path = Path(__file__).resolve().parents[2] / "server" / "plugins" / "mikrotik_scan" / "mikrotik.py"
    spec = importlib.util.spec_from_file_location("mikrotik_scan", module_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is missing_module:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module

    return module


mikrotik = _load_mikrotik_module()


def _lease(lease_id, address, mac_address, status="bound"):
    lease = {
        ".id": lease_id,
        "address": address,
        "host-name": f"device-{lease_id}",
        "comment": "",
        "last-seen": "1m",
        "status": status,
    }
    if mac_address is not None:
        lease["mac-address"] = mac_address
    return lease


def test_leases_without_mac_do_not_abort_remaining_leases():
    leases = [
        _lease("*1", "192.168.1.2", "aa-bb-cc-dd-ee-01"),
        _lease("*2", "192.168.1.5", None, status="waiting"),
        _lease("*3", "192.168.1.6", None),
        _lease("*4", "192.168.1.8", "aa-bb-cc-dd-ee-04"),
    ]
    api = MagicMock(return_value=leases)
    plugin_objects = MagicMock()

    mikrotik.MT_USER = "user"
    mikrotik.MT_PASS = None
    mikrotik.MT_HOST = "192.168.1.1"
    mikrotik.MT_PORT = 8728

    with patch.object(mikrotik, "connect", return_value=api):
        result = mikrotik.get_entries(plugin_objects)

    assert result is plugin_objects
    assert plugin_objects.add_object.call_count == 2
    assert [call.kwargs["primaryId"] for call in plugin_objects.add_object.call_args_list] == ["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:04"]
