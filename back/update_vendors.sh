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

echo "---------------------------------------------------------"
echo "[INSTALL]                           Run update_vendors.sh"
echo "---------------------------------------------------------"

DL_DIR=/usr/share/arp-scan

# ----------------------------------------------------------------------
echo Updating... $DL_DIR
cd $DL_DIR || { echo "could not enter $DL_DIR directory"; exit 1; }

# Define the URL of the IEEE OUI file
IEEE_OUI_URL="http://standards-oui.ieee.org/oui/oui.txt"

# Download the file using wget
wget "$IEEE_OUI_URL" -O ieee-oui_dl.txt

# Filter lines containing "(base 16)" and format them with a tab between MAC and vendor
grep "(base 16)" ieee-oui_dl.txt | sed -E 's/ *\(base 16\)//' | awk -F' ' '{printf "%s\t%s\n", $1, substr($0, index($0, $2))}' > ieee-oui_new.txt

# Combine, sort, and remove duplicates, ensuring tab-separated output
cat ieee-oui.txt ieee-oui_new.txt >> ieee-oui_all.txt
sort ieee-oui_all.txt | awk '{$1=$1; print}' | sort -u | awk -F' ' '{printf "%s\t%s\n", $1, substr($0, index($0, $2))}' > ieee-oui_all_filtered.txt



