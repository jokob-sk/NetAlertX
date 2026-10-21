"""
Unit tests for helper.py's count_children_by_parent_mac().

Tests verify the O(n) bucket-count replacement for the old per-device
O(n) scan (get_number_of_children) produces identical results.
"""

import sys
import os

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from helper import count_children_by_parent_mac  # noqa: E402


class TestCountChildrenByParentMac:
    """Test suite for count_children_by_parent_mac()"""

    def test_empty_list_returns_empty_dict(self):
        assert count_children_by_parent_mac([]) == {}

    def test_parent_with_two_children_and_a_grandchild(self):
        devices = [
            {"devMac": "aa:aa:aa:aa:aa:aa", "devParentMAC": ""},
            {"devMac": "bb:bb:bb:bb:bb:bb", "devParentMAC": "aa:aa:aa:aa:aa:aa"},
            {"devMac": "cc:cc:cc:cc:cc:cc", "devParentMAC": "aa:aa:aa:aa:aa:aa"},
            {"devMac": "dd:dd:dd:dd:dd:dd", "devParentMAC": "bb:bb:bb:bb:bb:bb"},
        ]

        counts = count_children_by_parent_mac(devices)

        assert counts["aa:aa:aa:aa:aa:aa"] == 2
        assert counts["bb:bb:bb:bb:bb:bb"] == 1
        # leaf devices are absent from the dict, not present with a 0 value
        assert "cc:cc:cc:cc:cc:cc" not in counts
        assert "dd:dd:dd:dd:dd:dd" not in counts

    def test_missing_or_empty_parent_mac_excluded(self):
        devices = [
            {"devMac": "aa:aa:aa:aa:aa:aa", "devParentMAC": ""},
            {"devMac": "bb:bb:bb:bb:bb:bb"},  # devParentMAC key absent entirely
        ]

        assert count_children_by_parent_mac(devices) == {}

    def test_result_independent_of_input_order(self):
        devices = [
            {"devMac": "bb:bb:bb:bb:bb:bb", "devParentMAC": "aa:aa:aa:aa:aa:aa"},
            {"devMac": "aa:aa:aa:aa:aa:aa", "devParentMAC": ""},
            {"devMac": "cc:cc:cc:cc:cc:cc", "devParentMAC": "aa:aa:aa:aa:aa:aa"},
        ]

        assert count_children_by_parent_mac(devices) == count_children_by_parent_mac(
            list(reversed(devices))
        )

    def test_lookup_uses_stripped_devmac_like_original(self):
        # Caller strips devMac before lookup (graphql_endpoint.py); the count
        # dict's keys must match that stripped form for the lookup to hit.
        devices = [
            {"devMac": "aa:aa:aa:aa:aa:aa", "devParentMAC": ""},
            {"devMac": "bb:bb:bb:bb:bb:bb", "devParentMAC": " aa:aa:aa:aa:aa:aa "},
        ]

        counts = count_children_by_parent_mac(devices)

        assert counts["aa:aa:aa:aa:aa:aa".strip()] == 1
