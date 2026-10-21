"""Tests for update_devPresentLastScan_based_on_nics.

Regression coverage for the bug where a parent device with a 'nic' child
relationship had its own directly-detected presence overwritten by the NIC
child's absence, producing an endless one-directional Connected event stream.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db_test_helpers import make_db, make_device_dict, insert_device_from_dict, DummyDB

from server.scan import device_handling


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(devices: list[dict]):
    """Return a DummyDB seeded with the given device dicts."""
    conn = make_db()
    for dev in devices:
        insert_device_from_dict(conn, dev)
    return DummyDB(conn)


def _present(db: DummyDB, mac: str) -> int:
    row = db._conn.execute(
        "SELECT devPresentLastScan FROM Devices WHERE devMac = ?", (mac,)
    ).fetchone()
    return row["devPresentLastScan"]


# ---------------------------------------------------------------------------
# Core bug regression: parent directly detected (present=1) + absent NIC child
# ---------------------------------------------------------------------------

class TestNicChildDoesNotForcePresentParentDown:
    """Parent was directly detected this scan; an absent NIC must not override that."""

    def test_any_mode_absent_nic_does_not_clear_present_parent(self):
        """Bug: req_all=0, parent present=1, nic present=0 → parent must stay 1."""
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:01", devPresentLastScan=1,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=0),
            make_device_dict("bb:bb:bb:bb:bb:01", devPresentLastScan=0,
                             devParentMAC="aa:aa:aa:aa:aa:01",
                             devParentRelType="nic", devReqNicsOnline=0),
        ])
        device_handling.update_devPresentLastScan_based_on_nics(db)
        assert _present(db, "aa:aa:aa:aa:aa:01") == 1, (
            "Parent directly detected as present must not be forced offline "
            "by an absent NIC child."
        )

    def test_req_all_mode_absent_nic_does_not_clear_present_parent(self):
        """Bug: req_all=1, parent present=1, nic present=0 → parent must stay 1."""
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:02", devPresentLastScan=1,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=1),
            make_device_dict("bb:bb:bb:bb:bb:02", devPresentLastScan=0,
                             devParentMAC="aa:aa:aa:aa:aa:02",
                             devParentRelType="nic", devReqNicsOnline=0),
        ])
        device_handling.update_devPresentLastScan_based_on_nics(db)
        assert _present(db, "aa:aa:aa:aa:aa:02") == 1


# ---------------------------------------------------------------------------
# NIC can still raise an undetected parent (original=0)
# ---------------------------------------------------------------------------

class TestNicRaisesAbsentParent:
    """NIC children should be able to mark a parent present when it was not seen directly."""

    def test_any_mode_online_nic_raises_absent_parent(self):
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:03", devPresentLastScan=0,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=0),
            make_device_dict("bb:bb:bb:bb:bb:03", devPresentLastScan=1,
                             devParentMAC="aa:aa:aa:aa:aa:03",
                             devParentRelType="nic", devReqNicsOnline=0),
        ])
        device_handling.update_devPresentLastScan_based_on_nics(db)
        assert _present(db, "aa:aa:aa:aa:aa:03") == 1

    def test_req_all_mode_all_nics_online_raises_absent_parent(self):
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:04", devPresentLastScan=0,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=1),
            make_device_dict("bb:bb:bb:bb:bb:04", devPresentLastScan=1,
                             devParentMAC="aa:aa:aa:aa:aa:04",
                             devParentRelType="nic", devReqNicsOnline=0),
            make_device_dict("cc:cc:cc:cc:cc:04", devPresentLastScan=1,
                             devParentMAC="aa:aa:aa:aa:aa:04",
                             devParentRelType="nic", devReqNicsOnline=0),
        ])
        device_handling.update_devPresentLastScan_based_on_nics(db)
        assert _present(db, "aa:aa:aa:aa:aa:04") == 1

    def test_req_all_mode_partial_nics_does_not_raise_absent_parent(self):
        """req_all=1: if not all NICs are online, an absent parent stays absent."""
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:05", devPresentLastScan=0,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=1),
            make_device_dict("bb:bb:bb:bb:bb:05", devPresentLastScan=1,
                             devParentMAC="aa:aa:aa:aa:aa:05",
                             devParentRelType="nic", devReqNicsOnline=0),
            make_device_dict("cc:cc:cc:cc:cc:05", devPresentLastScan=0,
                             devParentMAC="aa:aa:aa:aa:aa:05",
                             devParentRelType="nic", devReqNicsOnline=0),
        ])
        device_handling.update_devPresentLastScan_based_on_nics(db)
        assert _present(db, "aa:aa:aa:aa:aa:05") == 0

    def test_any_mode_all_nics_absent_leaves_parent_absent(self):
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:06", devPresentLastScan=0,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=0),
            make_device_dict("bb:bb:bb:bb:bb:06", devPresentLastScan=0,
                             devParentMAC="aa:aa:aa:aa:aa:06",
                             devParentRelType="nic", devReqNicsOnline=0),
        ])
        device_handling.update_devPresentLastScan_based_on_nics(db)
        assert _present(db, "aa:aa:aa:aa:aa:06") == 0


# ---------------------------------------------------------------------------
# No NIC children → no change regardless of presence
# ---------------------------------------------------------------------------

class TestNoNicChildren:
    def test_parent_with_no_nics_unchanged(self):
        db = _setup([
            make_device_dict("aa:aa:aa:aa:aa:07", devPresentLastScan=1,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=0),
            make_device_dict("aa:aa:aa:aa:aa:08", devPresentLastScan=0,
                             devParentMAC="", devParentRelType="", devReqNicsOnline=0),
        ])
        updated = device_handling.update_devPresentLastScan_based_on_nics(db)
        assert updated == 0
        assert _present(db, "aa:aa:aa:aa:aa:07") == 1
        assert _present(db, "aa:aa:aa:aa:aa:08") == 0
