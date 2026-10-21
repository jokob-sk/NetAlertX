"""
Shared constants for the workflow engine.

Centralised here so that manager, actions, and models can all import from a
single source of truth rather than duplicating schema knowledge across files.
"""

import re

# ---------------------------------------------------------------------------
# Devices table column whitelist
# ---------------------------------------------------------------------------

# Every column present in the Devices table schema.  Used in two ways:
#  1. Token validation — {{trigger.COLUMN}} tokens are rejected at workflow
#     load time if COLUMN is not in this set.
#  2. Query safety — queryByConditions() refuses to build WHERE clauses for
#     columns not in this set, preventing SQL injection via workflow JSON.
VALID_DEVICE_COLUMNS = frozenset([
    "devMac", "devName", "devOwner", "devType", "devVendor", "devFavorite",
    "devGroup", "devComments", "devFirstConnection", "devLastConnection",
    "devLastIP", "devPrimaryIPv4", "devPrimaryIPv6", "devVlan", "devForceStatus",
    "devStaticIP", "devScan", "devLogEvents", "devAlertEvents", "devAlertDown",
    "devSkipRepeated", "devLastNotification", "devPresentLastScan", "devIsNew",
    "devLocation", "devIsArchived", "devParentMAC", "devParentPort",
    "devParentRelType", "devIcon", "devGUID", "devSite", "devSSID",
    "devSyncHubNode", "devSourcePlugin", "devFQDN", "devMacSource",
    "devNameSource", "devFQDNSource", "devLastIPSource", "devVendorSource",
    "devSSIDSource", "devParentMACSource", "devParentPortSource",
    "devParentRelTypeSource", "devVlanSource", "devCustomProps",
])

# Devices table columns whose CHECK constraint requires a strict integer 0 or 1.
# Values destined for these columns are cast to int before being written to DB.
BOOLEAN_COLUMNS = frozenset([
    "devFavorite", "devStaticIP", "devLogEvents", "devAlertEvents",
    "devAlertDown", "devPresentLastScan", "devIsNew", "devIsArchived",
])

# Compiled regex for {{trigger.COLUMN_NAME}} token substitution and validation.
TOKEN_RE = re.compile(r"\{\{trigger\.(\w+)\}\}")
