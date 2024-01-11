#!/usr/bin/env bash

echo "---------------------------------------------------------"
echo "[INSTALL]                     Run install_dependencies.sh"
echo "---------------------------------------------------------"

# ❗ IMPORTANT - if you modify this file modify the root Dockerfile as well ❗

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

# alternate dependencies
sudo apt-get install nginx nginx-core mtr php-fpm php8.2-fpm php-cli php8.2 php8.2-sqlite3 -y
sudo phpenmod -v 8.2 sqlite3 

# setup virtual python environment so we can use pip3 to install packages
apt-get install python3.11-venv -y
python3 -m venv myenv
source myenv/bin/activate

update-alternatives --install /usr/bin/python python /usr/bin/python3 10

#  install packages thru pip3
pip3 install requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet
