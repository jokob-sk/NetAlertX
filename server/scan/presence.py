import re

_SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def current_scan_presence_condition(mac_column: str) -> str:
    """SQL fragment: TRUE if any CurrentScan row for mac_column asserts presence.
    The one and only definition of 'is this MAC present this cycle' - every
    caller uses this, nobody writes their own CurrentScan presence predicate.

    mac_column MUST be a trusted, hardcoded SQL column/table.column reference
    written by NetAlertX code (e.g. "devMac", "CurrentScan.scanMac") - this
    function does raw string interpolation, not parameterized SQL. Never pass
    plugin data, user input, or any runtime string value here.

    The inner CurrentScan is aliased as presence_scan so a qualified
    mac_column like "CurrentScan.scanMac" resolves to the outer reference,
    not this subquery's own row - without the alias the bare table name
    shadows it, turning the comparison into a same-row tautology that's
    true for any row with a non-NULL scanMac. mac_column may not reference
    presence_scan itself for the same reason.

    Not usable everywhere a presence check appears: the "New Connections"
    query in session_events.py and the raw Sessions insert in
    create_new_devices() (device_handling.py) both need the actual
    scanLastIP/scanVendor *values* off the presence-asserting row via a
    MIN()/GROUP BY aggregate, not just a boolean - see
    scan-pipeline-hardening.md Design §1's correction for why those two
    (plus "IP Changed", an eighth non-canonical site) keep their own
    hand-written aggregation instead of calling this helper.
    """
    if not _SQL_IDENTIFIER_RE.match(mac_column):
        raise ValueError(f"mac_column must be a plain identifier, got: {mac_column!r}")
    if mac_column == "presence_scan" or mac_column.startswith("presence_scan."):
        raise ValueError(
            f"mac_column must not reference presence_scan - that's this helper's own "
            f"internal subquery alias, got: {mac_column!r}"
        )
    return f"""EXISTS (
        SELECT 1 FROM CurrentScan AS presence_scan
        WHERE presence_scan.scanMac = {mac_column} AND presence_scan.scanPresence = 1
    )"""


def nic_derived_presence_condition(mac_column: str) -> str:
    """SQL fragment answering exactly: 'would NIC reconciliation
    (update_devPresentLastScan_based_on_nics(), step 7 of process_scan())
    consider mac_column present, based on this cycle's CurrentScan rows for
    its NIC children (devParentRelType = 'nic') and its own devReqNicsOnline
    (ANY vs ALL)?' It intentionally does not read or write
    Devices.devPresentLastScan - see nic-parent-orphan-disconnect-events.md's
    Invariant for why that's still equivalent to step 7's own answer within
    the same cycle (step 6 sets every device's devPresentLastScan, NIC
    children included, to exactly current_scan_presence_condition()'s value
    for this cycle, before step 7 ever reads it). Not a general-purpose
    presence predicate - it answers this one question, nothing broader.

    Deliberately NOT a replacement for current_scan_presence_condition() -
    composed with it via OR at each call site (insert_events()'s Device
    Down/Disconnected queries, update_devLastConnection_from_CurrentScan()).
    Deliberately does NOT replicate update_devPresentLastScan_based_on_nics()'s
    "parent was directly detected this scan" carve-out: that carve-out is
    redundant here, because a directly-detected parent already satisfies
    current_scan_presence_condition() on its own, and the two are OR'd.

    mac_column must be a trusted, hardcoded SQL column/table.column reference
    written by NetAlertX code - same constraint as
    current_scan_presence_condition(), enforced the same way.

    The inner Devices scan is aliased as nic_presence_parent, not the more
    obvious nic_parent, for the same shadowing reason
    current_scan_presence_condition() aliases its own inner CurrentScan as
    presence_scan rather than bare CurrentScan: a caller correlating this
    condition from a query that itself aliases its row as nic_parent (a
    natural name to pick, given this helper's own docstring uses it) would
    otherwise have mac_column="nic_parent.devMac" resolve to this
    subquery's own inner alias instead of the caller's outer row, collapsing
    the comparison into an always-true same-row tautology. mac_column may
    not reference nic_presence_parent for the same reason presence_scan is
    guarded below.

    mac_column MUST be qualified (e.g. "Devices.devMac", "DevicesView.devMac"
    - never bare "devMac"), unlike current_scan_presence_condition() where a
    bare column is fine. The reason is column, not alias, shadowing: this
    function's own inner scan is `FROM Devices`, and Devices has a devMac
    column, so an unqualified devMac in the substituted WHERE always
    resolves to *this* function's own inner row - SQL prefers the innermost
    enclosing scope for an unqualified name and only searches outward if the
    inner scope has no matching column, so it never even reaches the
    caller's outer row. (current_scan_presence_condition()'s inner scan is
    `FROM CurrentScan`, which has no devMac column, so a bare "devMac" there
    has nothing to bind to inward and correctly falls back outward.)
    Confirmed live: an unqualified caller made every device with no NIC
    children of its own read as NIC-derived-present, as soon as *any* other
    device anywhere in Devices legitimately had one.
    """
    if not _SQL_IDENTIFIER_RE.match(mac_column):
        raise ValueError(f"mac_column must be a plain identifier, got: {mac_column!r}")
    if "." not in mac_column:
        raise ValueError(
            f"mac_column must be qualified with the caller's own table/alias "
            f"(e.g. 'Devices.devMac', not bare 'devMac') - Devices (this "
            f"function's own inner scan) already has a devMac column, so an "
            f"unqualified reference always binds to this function's own inner "
            f"row instead of the caller's, got: {mac_column!r}"
        )
    if mac_column == "presence_scan" or mac_column.startswith("presence_scan."):
        raise ValueError(
            f"mac_column must not reference presence_scan - that's "
            f"current_scan_presence_condition()'s own internal subquery "
            f"alias, got: {mac_column!r}"
        )
    if mac_column == "nic_presence_parent" or mac_column.startswith("nic_presence_parent."):
        raise ValueError(
            f"mac_column must not reference nic_presence_parent - that's "
            f"this function's own internal subquery alias, got: {mac_column!r}"
        )

    return f"""EXISTS (
        SELECT 1 FROM Devices AS nic_presence_parent
        WHERE nic_presence_parent.devMac = {mac_column}
          AND (
                (
                    IFNULL(CAST(nic_presence_parent.devReqNicsOnline AS TEXT), '') = '1'
                    AND EXISTS (SELECT 1 FROM Devices AS any_nic
                                WHERE any_nic.devParentMAC = nic_presence_parent.devMac
                                  AND any_nic.devParentRelType = 'nic')
                    AND NOT EXISTS (
                        SELECT 1 FROM Devices AS nic
                        WHERE nic.devParentMAC = nic_presence_parent.devMac
                          AND nic.devParentRelType = 'nic'
                          AND NOT {current_scan_presence_condition("nic.devMac")}
                    )
                )
                OR
                (
                    IFNULL(CAST(nic_presence_parent.devReqNicsOnline AS TEXT), '') != '1'
                    AND EXISTS (
                        SELECT 1 FROM Devices AS nic
                        WHERE nic.devParentMAC = nic_presence_parent.devMac
                          AND nic.devParentRelType = 'nic'
                          AND {current_scan_presence_condition("nic.devMac")}
                    )
                )
          )
    )"""
