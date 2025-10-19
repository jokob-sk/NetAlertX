#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
#  NetAlertX
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  update_vendors.sh - Back module. IEEE Vendors db update
# ------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
# ------------------------------------------------------------------------------

# ----------------------------------------------------------------------
#  Main directories to update:
#    /usr/share/arp-scan
# ----------------------------------------------------------------------

#!/usr/bin/env bash
set -euo pipefail

TEMP_FILE="/services/run/tmp/ieee-oui.txt.tmp"
OUTPUT_FILE="/services/run/tmp/ieee-oui.txt"

# Download the file using wget to stdout and process it
if ! wget --timeout=30 --tries=3 "https://standards-oui.ieee.org/oui/oui.txt" -O /dev/stdout | \
	sed -E 's/ *\(base 16\)//' | \
	awk -F' ' '{printf "%s\t%s\n", $1, substr($0, index($0, $2))}' | \
	sort | \
	awk '{$1=$1; print}' | \
	sort -u | \
	awk -F' ' '{printf "%s\t%s\n", $1, substr($0, index($0, $2))}' \
	> "${TEMP_FILE}"; then
	echo "ERROR: Failed to download or process OUI data" >&2
	rm -f "${TEMP_FILE}"
	exit 1
fi

# Validate we got actual content (should have hundreds of thousands of lines)
if [ ! -s "${TEMP_FILE}" ] || [ "$(wc -l < "${TEMP_FILE}")" -lt 1000 ]; then
	echo "ERROR: OUI data appears invalid or incomplete" >&2
	rm -f "${TEMP_FILE}"
	exit 1
fi

# Atomic replacement
mv "${TEMP_FILE}" "${OUTPUT_FILE}"
echo "Successfully updated IEEE OUI database ($(wc -l < "${OUTPUT_FILE}") entries)"
    > /services/run/tmp/ieee-oui.txt

