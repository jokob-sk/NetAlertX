#!/bin/bash

echo "---------------------------------------------------------"
echo "[INSTALL]                     Run install_dependencies.sh"
echo "---------------------------------------------------------"

# Set environment variables
INSTALL_DIR=/home/pi  # Specify the installation directory here

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi


# Install dependencies
apt-get install -y \
    tini snmp ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo \
    nginx-light php php-cgi php-fpm php-sqlite3 php-curl sqlite3 dnsutils net-tools \
    python3 iproute2 nmap python3-pip zip systemctl usbutils traceroute

# ---------------------------------------------------------------
# alternate dependencies
# sudo apt-get install mtr-tiny -y
sudo apt-get install nginx nginx-core mtr php-fpm php8.2-fpm -y
sudo apt-get install php-cli php8.2 php8.2-fpm -y
sudo apt-get install php8.2-sqlite3 -y
sudo phpenmod -v 8.2 sqlite3 
# sudo apt-get install net-tools -y
# ---------------------------------------------------------------
