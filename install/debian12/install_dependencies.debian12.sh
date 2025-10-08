#!/usr/bin/env bash

echo "---------------------------------------------------------"
echo "[INSTALL]            Run install_dependencies.debian12.sh"
echo "---------------------------------------------------------"

# ❗ IMPORTANT - if you modify this file modify the root Dockerfile as well ❗

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi

# Install dependencies
apt-get install -y \
    tini snmp ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo gettext-base \
    nginx-light php php-cgi php-fpm php-sqlite3 php-curl sqlite3 dnsutils net-tools \
    python3 python3-dev iproute2 nmap python3-pip zip usbutils traceroute nbtscan avahi-daemon avahi-utils openrc build-essential git

# alternate dependencies
sudo apt-get install nginx nginx-core mtr php-fpm php8.2-fpm php-cli php8.2 php8.2-sqlite3 -y
sudo phpenmod -v 8.2 sqlite3 

# setup virtual python environment so we can use pip3 to install packages
apt-get install python3-venv -y
python3 -m venv /opt/venv
source /opt/venv/bin/activate

update-alternatives --install /usr/bin/python python /usr/bin/python3 10

#  install packages thru pip3
pip3 install openwrt-luci-rpc asusrouter asyncio aiohttp graphene flask flask-cors unifi-sm-api tplink-omada-client wakeonlan pycryptodome requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet python-nmap dnspython librouteros yattag git+https://github.com/foreign-sub/aiofreepybox.git 
