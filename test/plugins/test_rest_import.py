"""
Tests for the REST Import plugin (rest_import.py).

Module-level side effects (get_setting_value, Logger, Plugin_Objects,
conf.tz) are patched before import to prevent live config reads,
log file creation, or network calls during tests.
"""

import sys
import os
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_SERVER = os.path.join(_ROOT, 'server')
_PLUGINS = os.path.join(_ROOT, 'server', 'plugins')
_PLUGIN_DIR = os.path.join(_ROOT, 'server', 'plugins', 'rest_import')

for _p in [_ROOT, _SERVER, _PLUGINS, _PLUGIN_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Import module with side effects patched
# ---------------------------------------------------------------------------

with patch('helper.get_setting_value', return_value='UTC'), \
     patch('logger.Logger'), \
     patch('plugin_helper.Plugin_Objects'):
    import rest_import  # noqa: E402

from utils.crypto_utils import string_to_fake_mac  # noqa: E402


# ---------------------------------------------------------------------------
# build_headers
# ---------------------------------------------------------------------------

class TestBuildHeaders:
    def test_empty_string_returns_empty_dict(self):
        assert rest_import.build_headers('') == {}

    def test_none_returns_empty_dict(self):
        assert rest_import.build_headers(None) == {}

    def test_single_header(self):
        result = rest_import.build_headers('Accept: application/json')
        assert result == {'Accept': 'application/json'}

    def test_multiple_headers(self):
        raw = 'Accept: application/json\nX-API-Key: abc123'
        result = rest_import.build_headers(raw)
        assert result == {'Accept': 'application/json', 'X-API-Key': 'abc123'}

    def test_value_with_colon_preserved(self):
        result = rest_import.build_headers('Authorization: Bearer tok:en')
        assert result == {'Authorization': 'Bearer tok:en'}

    def test_malformed_line_without_colon_is_skipped(self):
        result = rest_import.build_headers('nocolonhere\nValid: yes')
        assert result == {'Valid': 'yes'}

    def test_blank_lines_skipped(self):
        result = rest_import.build_headers('\n  \nAccept: text/plain\n')
        assert result == {'Accept': 'text/plain'}


# ---------------------------------------------------------------------------
# resolve_path
# ---------------------------------------------------------------------------

class TestResolvePath:
    def test_empty_path_with_list_response(self):
        data = [{'mac': 'AA:BB:CC:DD:EE:FF'}]
        result = rest_import.resolve_path('test', data, '')
        assert result == data

    def test_flat_key(self):
        data = {'rows': [{'mac': 'AA:BB:CC:DD:EE:FF'}]}
        result = rest_import.resolve_path('test', data, 'rows')
        assert result == data['rows']

    def test_dot_notation(self):
        data = {'data': {'devices': [{'mac': 'AA:BB:CC:DD:EE:FF'}]}}
        result = rest_import.resolve_path('test', data, 'data.devices')
        assert result == data['data']['devices']

    def test_missing_path_returns_none(self):
        data = {'rows': []}
        result = rest_import.resolve_path('test', data, 'missing.key')
        assert result is None

    def test_path_points_to_non_list_returns_none(self):
        data = {'rows': {'not': 'a list'}}
        result = rest_import.resolve_path('test', data, 'rows')
        assert result is None

    def test_empty_path_non_list_response_returns_none(self):
        result = rest_import.resolve_path('test', {'key': 'value'}, '')
        assert result is None


# ---------------------------------------------------------------------------
# validate_mac
# ---------------------------------------------------------------------------

class TestValidateMac:
    def test_colon_separated_valid(self):
        mac = rest_import.validate_mac('AA:BB:CC:DD:EE:FF')
        assert mac is not None

    def test_dash_separated_valid(self):
        mac = rest_import.validate_mac('AA-BB-CC-DD-EE-FF')
        assert mac is not None

    def test_bare_hex_valid(self):
        mac = rest_import.validate_mac('AABBCCDDEEFF')
        assert mac is not None

    def test_invalid_string_returns_none(self):
        assert rest_import.validate_mac('not-a-mac') is None

    def test_empty_returns_none(self):
        assert rest_import.validate_mac('') is None

    def test_placeholder_unknown_returns_none(self):
        assert rest_import.validate_mac('unknown') is None

    def test_placeholder_star_returns_none(self):
        assert rest_import.validate_mac('*') is None

    def test_null_string_returns_none(self):
        assert rest_import.validate_mac('null') is None


# ---------------------------------------------------------------------------
# map_record
# ---------------------------------------------------------------------------

class TestMapRecord:
    def _cfg(self, mac_field='hwaddr', ip_field='address', fake_mac=False, **extra):
        cfg = {
            'RSTIMPRT_scanMac': mac_field,
            'RSTIMPRT_scanLastIP': ip_field,
            'RSTIMPRT_scanName': 'hostname',
            'RSTIMPRT_scanVendor': '',
            'RSTIMPRT_scanSSID': '',
            'RSTIMPRT_scanType': '',
            'RSTIMPRT_scanParentMAC': '',
            'RSTIMPRT_scanParentPort': '',
            'RSTIMPRT_scanSite': '',
            'RSTIMPRT_scanVlan': '',
            'RSTIMPRT_fake_mac': fake_mac,
        }
        cfg.update(extra)
        return cfg

    def test_valid_record_returns_dict(self):
        record = {'hwaddr': 'AA:BB:CC:DD:EE:FF', 'address': '192.168.1.10', 'hostname': 'mydevice'}
        cfg = self._cfg()
        result = rest_import.map_record('test', 0, record, cfg, 'hwaddr', 'address', False)
        assert result is not None
        assert result['ip'] == '192.168.1.10'
        assert result['name'] == 'mydevice'

    def test_invalid_mac_without_fake_mac_returns_none(self):
        record = {'hwaddr': 'not-a-mac', 'address': '192.168.1.10'}
        cfg = self._cfg()
        result = rest_import.map_record('test', 0, record, cfg, 'hwaddr', 'address', False)
        assert result is None

    def test_missing_mac_with_fake_mac_enabled_generates_mac(self):
        record = {'address': '192.168.1.50', 'hostname': 'server01'}
        cfg = self._cfg(mac_field='', fake_mac=True)
        result = rest_import.map_record('test', 0, record, cfg, '', 'address', True)
        assert result is not None
        expected_mac = string_to_fake_mac('192.168.1.50')
        assert result['mac'] == expected_mac

    def test_fake_mac_enabled_but_no_ip_returns_none(self):
        record = {'hostname': 'noip'}
        cfg = self._cfg(mac_field='', ip_field='', fake_mac=True)
        result = rest_import.map_record('test', 0, record, cfg, '', '', True)
        assert result is None

    def test_optional_fields_default_to_empty_when_not_configured(self):
        record = {'hwaddr': 'AA:BB:CC:DD:EE:FF', 'address': '10.0.0.1'}
        cfg = self._cfg()
        result = rest_import.map_record('test', 0, record, cfg, 'hwaddr', 'address', False)
        assert result is not None
        assert result['vendor'] == ''
        assert result['ssid'] == ''
        assert result['vlan'] == ''

    def test_valid_mac_takes_precedence_over_fake_mac_setting(self):
        record = {'hwaddr': 'AA:BB:CC:DD:EE:FF', 'address': '192.168.1.10'}
        cfg = self._cfg(fake_mac=True)
        result = rest_import.map_record('test', 0, record, cfg, 'hwaddr', 'address', True)
        assert result is not None
        # Should use the real MAC, not a fake one
        assert not result['mac'].startswith('fa:ce:')


# ---------------------------------------------------------------------------
# build_auth
# ---------------------------------------------------------------------------

class TestBuildAuth:
    def test_none_auth_returns_none(self):
        headers = {}
        auth = rest_import.build_auth('none', 'user', 'pass', 'token', headers)
        assert auth is None

    def test_basic_auth_returns_tuple(self):
        headers = {}
        auth = rest_import.build_auth('basic', 'myuser', 'mypass', '', headers)
        assert auth == ('myuser', 'mypass')

    def test_bearer_auth_injects_header(self):
        headers = {}
        auth = rest_import.build_auth('bearer', '', '', 'mytoken', headers)
        assert auth is None
        assert headers.get('Authorization') == 'Bearer mytoken'

    def test_basic_auth_without_username_returns_none(self):
        headers = {}
        auth = rest_import.build_auth('basic', '', 'pass', '', headers)
        assert auth is None

    def test_bearer_without_token_does_not_inject_header(self):
        headers = {}
        rest_import.build_auth('bearer', '', '', '', headers)
        assert 'Authorization' not in headers
