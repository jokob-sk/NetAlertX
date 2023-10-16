#!/bin/bash

# apt-get install python3-requests python3-paho-mqtt python3-scapy -y
echo "---------------------------------------------------------"
echo "[INSTALL]                           Run install_python.sh"
echo "---------------------------------------------------------"

# setup virtual python environment so we can use pip3 to install packages
apt-get install python3.11-venv -y
python3 -m venv myenv
source myenv/bin/activate

update-alternatives --install /usr/bin/python python /usr/bin/python3 10

#  install packages thru pip3
pip3 install requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet

