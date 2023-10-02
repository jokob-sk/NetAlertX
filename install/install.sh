#!/bin/bash

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi

# Set environment variables
PORT=20211
INSTALL_DIR=/home/pi  # Specify the installation directory here

# Update and upgrade system packages
# apt-get update
# apt-get upgrade -y

# Install Git
apt-get install -y git

# Clone the application repository
git clone https://github.com/jokob-sk/Pi.Alert "$INSTALL_DIR/pialert"

# Install dependencies
apt-get install -y \
    tini snmp ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo \
    nginx-light php php-cgi php-fpm php-sqlite3 php-curl sqlite3 dnsutils net-tools \
    python3 iproute2 nmap python3-pip zip systemctl usbutils traceroute

# ---------------------------------------------------------------
# alternate dependencies
sudo apt-get install -y \
    nginx nginx-core mtr mtr-tiny php-fpm php7.4-fpm 

sudo apt install php-cli php7.4 php7.4-fpm -y
sudo apt install php7.4-sqlite3 -y

sudo phpenmod -v 7.4 sqlite3 
sudo apt install net-tools -y

curl -sSL https://bootstrap.pypa.io/get-pip.py | python3
# ---------------------------------------------------------------

# Install Python packages
pip3 install requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi

# Update alternatives for Python
update-alternatives --install /usr/bin/python python /usr/bin/python3 10

# Configure Nginx
echo "Configure Nginx"
echo "---------------------------------------------------------------"


sudo rm -R /var/www/html 
ln -s $INSTALL_DIR/pialert/front /var/www/html 
sudo rm /etc/nginx/sites-available/default
sudo ln -s "$INSTALL_DIR/pialert/install/default" /etc/nginx/sites-available/default
sudo sed -i 's/listen 80/listen '"$PORT"'/g' /etc/nginx/sites-available/default

echo "Run the hardware vendors update"
echo "---------------------------------------------------------------"
# Run the hardware vendors update
"$INSTALL_DIR/pialert/back/update_vendors.sh"

# Create a backup of pialert.conf
cp "$INSTALL_DIR/pialert/config/pialert.conf" "$INSTALL_DIR/pialert/back/pialert.conf_bak"

# Create a backup of pialert.db
cp "$INSTALL_DIR/pialert/db/pialert.db" "$INSTALL_DIR/pialert/back/pialert.db_bak"

# Create buildtimestamp.txt
date +%s > "$INSTALL_DIR/pialert/front/buildtimestamp.txt"

chmod -R a+rwx $INSTALL_DIR
chmod -R a+rwx /var/www/html
chmod -R a+rw $INSTALL_DIR/front/log
chmod -R a+rw $INSTALL_DIR/config

/etc/init.d/php7.4-fpm start
# /etc/init.d/php8.2-fpm start
/etc/init.d/nginx start

# Start Nginx and your application to start at boot (if needed)
systemctl start nginx
systemctl enable nginx
systemctl enable pi-alert
sudo systemctl restart nginx

# Provide instructions or additional setup if needed
echo "Installation completed. Please configure any additional settings for your application."


cd $INSTALL_DIR/pialert

"$INSTALL_DIR/pialert/dockerfiles/start.sh"

# Exit the script
exit 0
