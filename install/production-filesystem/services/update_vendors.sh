#!/usr/bin/env bash

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

# Download the file using wget to stdout and process it
wget -q "https://standards-oui.ieee.org/oui/oui.txt" -O /dev/stdout | \
    sed -E 's/ *\(base 16\)//' | \
    awk -F' ' '{printf "%s\t%s\n", $1, substr($0, index($0, $2))}' | \
    sort | \
    awk '{$1=$1; print}' | \
    sort -u | \
    awk -F' ' '{printf "%s\t%s\n", $1, substr($0, index($0, $2))}' \
    > /services/run/tmp/ieee-oui.txt

