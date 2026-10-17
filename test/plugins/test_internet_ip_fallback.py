"""
Tests for internet_ip/script.py's curl fallback (INTRNT plugin).

The fallback validates its result against an IPv4-only regex, so it must ask
curl for an IPv4 address. On a dual-stack host without the IPv4 flag, curl can
answer with the host's public IPv6 address, which the regex then rejects,
making the plugin record 0.0.0.0 even though the internet is reachable
(netalertx/NetAlertX#1845). The call is also bounded in time so a hung
fallback cannot burn the plugin's whole RUN_TIMEOUT budget.

Run from inside the NetAlertX container (where the full environment is
available), or locally - in that case the NetAlertX-specific modules are
stubbed out automatically before the script is imported.

    pytest test/plugins/test_internet_ip_fallback.py -v
"""

import importlib.util
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub NetAlertX-specific modules so tests can run outside the container.
# These stubs are only placeholders for the duration of the `import script`
# below - they are popped from sys.modules again right after, so they don't
# leak into other test files sharing the same pytest session (which would
# otherwise shadow the real modules for every subsequent test).
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
_stub("const", logPath=_tmp_log)
_stub("plugin_helper", Plugin_Objects=MagicMock)
_stub("utils")
_stub("utils.datetime_utils", timeNowUTC=lambda: "2026-01-01 00:00:00")
_stub("logger", mylog=lambda *a: None, Logger=MagicMock, append_line_to_file=lambda *a: None)
_stub("helper", check_IP_format=lambda v: v, get_setting_value=lambda k, default="": "UTC")

# Load by explicit path under a unique module name. A bare `import script`
# would collide in sys.modules with whichever other plugin's script.py was
# imported first in the same pytest session - every plugin's entry point is
# named script.py, so the plain name is ambiguous.
_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "server", "plugins", "internet_ip", "script.py"
)
_spec = importlib.util.spec_from_file_location("internet_ip_script", _SCRIPT_PATH)
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(script)

fallback_check_ip = script.fallback_check_ip
no_internet_ip = script.no_internet_ip

for _name in _stubbed_module_names:
    sys.modules.pop(_name, None)


def _run_fallback(curl_stdout):
    """Call fallback_check_ip() with curl's stdout faked, returning
    (ip, message, argv-curl-was-called-with)."""
    with patch.object(script.subprocess, "check_output", return_value=curl_stdout) as mocked:
        ip, message = fallback_check_ip()
    return ip, message, mocked.call_args[0][0]


class TestForcesIPv4:
    """The regex that validates the result accepts only IPv4, so the request
    itself has to be IPv4, otherwise a dual-stack host gets a valid IPv6
    answer that is then thrown away (#1845)."""

    def test_curl_is_asked_for_ipv4(self):
        _, _, argv = _run_fallback("203.0.113.7\n")
        assert "-4" in argv

    def test_ipv4_response_is_accepted(self):
        ip, _, _ = _run_fallback("203.0.113.7\n")
        assert ip == "203.0.113.7"

    def test_ipv6_response_is_still_rejected(self):
        """Forcing IPv4 does not make the validation laxer: if a response is
        somehow IPv6 anyway, it must not be stored as the public IP."""
        ip, _, _ = _run_fallback("2001:db8::1\n")
        assert ip == no_internet_ip


class TestRequestIsBounded:
    """INTRNT_RUN_TIMEOUT is the whole subprocess's kill-timeout, enforced by
    the plugin runner - an unbounded fallback can burn it and get the process
    killed before it writes its result file."""

    def test_connect_and_total_time_are_capped(self):
        _, _, argv = _run_fallback("203.0.113.7\n")
        assert "--connect-timeout" in argv
        assert "--max-time" in argv

    def test_subprocess_call_passes_an_explicit_timeout(self):
        """CLAUDE.md: every subprocess call needs an explicit timeout, not
        only the called program's own time limit."""
        with patch.object(script.subprocess, "check_output", return_value="203.0.113.7\n") as mocked:
            fallback_check_ip()
        assert mocked.call_args.kwargs.get("timeout") is not None

    def test_timeout_is_reported_not_raised(self):
        """A timed-out fallback returns the no-internet sentinel rather than
        propagating and killing the run."""
        with patch.object(script.subprocess, "check_output", side_effect=Exception("timed out")):
            ip, message = fallback_check_ip()
        assert ip == no_internet_ip
        assert "timed out" in message


class TestUsesHttps:
    def test_endpoint_is_https(self):
        _, _, argv = _run_fallback("203.0.113.7\n")
        assert argv[-1].startswith("https://")
