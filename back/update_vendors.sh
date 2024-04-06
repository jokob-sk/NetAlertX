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
#    /usr/share/ieee-data
#    /var/lib/ieee-data
# ----------------------------------------------------------------------
echo "---------------------------------------------------------"
echo "[INSTALL]                           Run update_vendors.sh"
echo "---------------------------------------------------------"

# ----------------------------------------------------------------------
echo Updating... /usr/share/ieee-data/
cd /usr/share/ieee-data/ || { echo "could not enter /usr/share/ieee-data directory"; exit 1; }

sudo mkdir -p 2_backup
sudo cp -- *.txt 2_backup
sudo cp -- *.csv 2_backup
echo ""
echo Download Start
echo ""
sudo curl "$1" -LO https://standards-oui.ieee.org/oui28/mam.csv \              
              -LO https://standards-oui.ieee.org/oui28/mam.csv \
              -LO https://standards-oui.ieee.org/oui28/mam.txt \
              -LO https://standards-oui.ieee.org/oui36/oui36.csv \
              -LO https://standards-oui.ieee.org/oui36/oui36.txt \
              -LO https://standards-oui.ieee.org/oui/oui.csv \
              -LO https://standards-oui.ieee.org/oui/oui.txt
echo ""
echo Download Finished

# ----------------------------------------------------------------------
echo ""
echo Updating... /usr/share/arp-scan/
cd /usr/share/arp-scan || { echo "could not enter /usr/share/arp-scan directory"; exit 1; }

sudo mkdir -p 2_backup
sudo cp -- *.txt 2_backup

# Update from /usb/lib/ieee-data
sudo get-iab -v
sudo get-oui -v

# make files readable
sudo chmod +r /usr/share/arp-scan/ieee-oui.txt

# Update from ieee website
# sudo get-iab -v -u http://standards-oui.ieee.org/iab/iab.txt
# sudo get-oui -v -u http://standards-oui.ieee.org/oui/oui.txt

# Update from ieee website develop
# sudo get-iab -v -u http://standards.ieee.org/develop/regauth/iab/iab.txt
# sudo get-oui -v -u http://standards.ieee.org/develop/regauth/oui/oui.txt

# Update from Sanitized oui (linuxnet.ca)
# sudo get-oui -v -u https://linuxnet.ca/ieee/oui.txt

