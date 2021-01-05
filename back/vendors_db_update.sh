#!/bin/sh
#
# Update MAC Vendor DB
#
# /usr/share/arp-scan
# /usr/share/ieee-data
# /var/lib/ieee-data
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
echo Updating... /usr/share/ieee-data/
cd /usr/share/ieee-data/

sudo mkdir -p 2_backup
sudo cp *.txt 2_backup
sudo cp *.csv 2_backup

sudo curl -# -O http://standards-oui.ieee.org/iab/iab.csv
sudo curl -# -O http://standards-oui.ieee.org/iab/iab.txt

sudo curl -# -O http://standards-oui.ieee.org/oui28/mam.csv
sudo curl -# -O http://standards-oui.ieee.org/oui28/mam.txt

sudo curl -# -O http://standards-oui.ieee.org/oui36/oui36.csv
sudo curl -# -O http://standards-oui.ieee.org/oui36/oui36.txt

sudo curl -# -O http://standards-oui.ieee.org/oui/oui.csv
sudo curl -# -O http://standards-oui.ieee.org/oui/oui.txt


# ----------------------------------------------------------------------
echo ""
echo Updating... /usr/share/arp-scan/
cd /usr/share/arp-scan

sudo mkdir -p 2_backup
sudo cp *.txt 2_backup

# Update from /usb/lib/ieee-data
sudo get-iab -v
sudo get-oui -v

# Update from ieee website
# sudo get-iab -v -u http://standards-oui.ieee.org/iab/iab.txt
# sudo get-oui -v -u http://standards-oui.ieee.org/oui/oui.txt

# Update from ieee website develop
# sudo get-iab -v -u http://standards.ieee.org/develop/regauth/iab/iab.txt
# sudo get-oui -v -u http://standards.ieee.org/develop/regauth/oui/oui.txt

# Update from Sanitized oui (linuxnet.ca)
# sudo get-oui -v -u https://linuxnet.ca/ieee/oui.txt

