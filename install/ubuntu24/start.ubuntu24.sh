#!/usr/bin/env bash

echo "---------------------------------------------------------"
echo "[INSTALL]"
echo "---------------------------------------------------------"
echo
echo "This script will set up and start NetAlertX on your Ubuntu24 system."

# Specify the installation directory here
INSTALL_DIR=/app

# DO NOT CHANGE ANYTHING BELOW THIS LINE!
INSTALLER_DIR=$INSTALL_DIR/install/ubuntu24
CONF_FILE=app.conf
DB_FILE=app.db
NGINX_CONF_FILE=netalertx.conf
WEB_UI_DIR=/var/www/html/netalertx
NGINX_CONFIG_FILE=/etc/nginx/conf.d/$NGINX_CONF_FILE
OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt
INSTALL_PATH=$INSTALL_DIR
FILEDB=$INSTALL_PATH/db/$DB_FILE
PHPVERSION="8.3"
# DO NOT CHANGE ANYTHING ABOVE THIS LINE!

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then    
  FILECONF=$INSTALL_PATH/config/$CONF_FILE 
  if [ -f "$FILECONF" ]; then
    sed -i -e "s|Europe/Berlin|${TZ}|g" "$INSTALL_PATH/config/$CONF_FILE"
  else 
    sed -i -e "s|Europe/Berlin|${TZ}|g" "$INSTALL_PATH/back/$CONF_FILE.bak"
  fi
fi


# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi



echo "---------------------------------------------------------"
echo "[INSTALL] Installing dependencies"
echo "---------------------------------------------------------"
echo


# Install dependencies
apt-get install -y \
    tini snmp ca-certificates curl libwww-perl arp-scan perl apt-utils cron \
    nginx-light php php-cgi php-fpm php-sqlite3 php-curl sqlite3 dnsutils net-tools \
    python3 python3-dev iproute2 nmap python3-pip zip usbutils traceroute nbtscan avahi-daemon avahi-utils build-essential

# alternate dependencies
apt-get install nginx nginx-core mtr php-fpm php${PHPVERSION}-fpm php-cli php${PHPVERSION} php${PHPVERSION}-sqlite3 -y
phpenmod -v ${PHPVERSION} sqlite3

update-alternatives --install /usr/bin/python python /usr/bin/python3 10

cd $INSTALLER_DIR || { echo "Failed to change directory to $INSTALLER_DIR"; exit 1; }

# setup virtual python environment so we can use pip3 to install packages
apt-get install python3-venv -y
python3 -m venv myenv
source myenv/bin/activate

#  install packages thru pip3
pip3 install openwrt-luci-rpc asusrouter asyncio aiohttp graphene flask flask-cors unifi-sm-api tplink-omada-client wakeonlan pycryptodome requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet python-nmap dnspython librouteros yattag git+https://github.com/foreign-sub/aiofreepybox.git 




echo "---------------------------------------------------------"
echo "[INSTALL] Installing NGINX and setting up the web server"
echo "---------------------------------------------------------"
echo
echo "[INSTALL] Stopping any NGINX web server"

service nginx stop 2>/dev/null
pkill -f "python ${INSTALL_DIR}/server" 2>/dev/null
echo "[INSTALL] Updating the existing installation..."

# Remove default NGINX site if it is symlinked, or backup it otherwise
if [ -L /etc/nginx/sites-enabled/default ] ; then
  echo "[INSTALL] Disabling default NGINX site, removing sym-link in /etc/nginx/sites-enabled"
  rm /etc/nginx/sites-enabled/default
elif [ -f /etc/nginx/sites-enabled/default ]; then
  echo "[INSTALL] Disabling default NGINX site, moving config to /etc/nginx/sites-available"
  mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.bkp_netalertx
fi

# Clear existing directories and files
if [ -d $WEB_UI_DIR ]; then
  echo "[INSTALL] Removing existing NetAlertX web-UI"
  rm -R $WEB_UI_DIR
fi

echo "[INSTALL] Removing existing NetAlertX NGINX config"
rm "$NGINX_CONFIG_FILE" 2>/dev/null || true

# create symbolic link to the  install directory
ln -s $INSTALL_PATH/front $WEB_UI_DIR
# create symbolic link to NGINX configuration coming with NetAlertX
ln -s "${INSTALLER_DIR}/$NGINX_CONF_FILE" $NGINX_CONFIG_FILE

# Use user-supplied port if set
if [ -n "${PORT}" ]; then
  echo "[INSTALL] Setting webserver to user-supplied port ($PORT)"
  sed -i 's/listen 20211/listen '"$PORT"'/g' "$NGINX_CONFIG_FILE"
fi

# Change web interface address if set
if [ -n "${LISTEN_ADDR}" ]; then
  echo "[INSTALL] Setting webserver to user-supplied address (${LISTEN_ADDR})"
  sed -i -e 's/listen /listen '"${LISTEN_ADDR}":'/g' "$NGINX_CONFIG_FILE"
fi

# Change php version
echo "[INSTALL] Setting PHP version to ${PHPVERSION}"
sed -i 's#unix:/run/php/php8.3-fpm.sock#unix:/run/php/php'"${PHPVERSION}"'-fpm.sock#ig' $NGINX_CONFIG_FILE

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "$OUI_FILE" ]; then
  echo "[INSTALL] The file ieee-oui.txt exists. Skipping update_vendors.sh..."
else
  echo "[INSTALL] The file ieee-oui.txt does not exist. Running update_vendors..."

  # Run the update_vendors.sh script
  if [ -f "${INSTALL_PATH}/back/update_vendors.sh" ]; then
    "${INSTALL_PATH}/back/update_vendors.sh"
  else
    echo "[INSTALL] update_vendors.sh script not found in $INSTALL_DIR."    
  fi
fi

echo "---------------------------------------------------------"
echo "[INSTALL] Create log and api mounts"
echo "---------------------------------------------------------"
echo

echo "[INSTALL] Cleaning up old mounts if any"
umount "${INSTALL_DIR}/log"
umount "${INSTALL_DIR}/api"

echo "[INSTALL] Creating log and api folders if they don't exist"
mkdir -p "${INSTALL_DIR}/log" "${INSTALL_DIR}/api"

echo "[INSTALL] Mounting log and api folders as tmpfs"
mount -t tmpfs -o noexec,nosuid,nodev tmpfs "${INSTALL_DIR}/log"
mount -t tmpfs -o noexec,nosuid,nodev tmpfs "${INSTALL_DIR}/api"


# Create log files if they don't exist
echo "[INSTALL] Creating log files if they don't exist"
touch "${INSTALL_DIR}"/log/{app.log,execution_queue.log,app_front.log,app.php_errors.log,stderr.log,stdout.log,db_is_locked.log}
touch "${INSTALL_DIR}"/api/user_notifications.json
# Create plugins sub-directory if it doesn't exist in case a custom log folder is used
mkdir -p "${INSTALL_DIR}"/log/plugins


# Fixing file permissions
echo "[INSTALL] Fixing file permissions"
chown root:www-data "${INSTALL_DIR}"/api/user_notifications.json

echo "[INSTALL] Fixing WEB_UI_DIR: ${WEB_UI_DIR}"

chmod -R a+rwx $WEB_UI_DIR

echo "[INSTALL] Fixing INSTALL_DIR: ${INSTALL_DIR}"

chmod -R a+rw $INSTALL_PATH/log
chmod -R a+rwx $INSTALL_DIR

echo "[INSTALL] Copy starter $DB_FILE and $CONF_FILE if they don't exist"


# DANGER ZONE: ALWAYS_FRESH_INSTALL 
if [ "$ALWAYS_FRESH_INSTALL" = true ]; then
  echo "[INSTALL] ❗ ALERT /db and /config folders are cleared because the ALWAYS_FRESH_INSTALL is set to: ${ALWAYS_FRESH_INSTALL}❗"
  # Delete content of "/config/"
  rm -rf "${INSTALL_PATH}/config/"*
  
  # Delete content of "/db/"
  rm -rf "${INSTALL_PATH}/db/"*
fi


# Copy starter $DB_FILE and $CONF_FILE if they don't exist
cp --update=none "${INSTALL_PATH}/back/$CONF_FILE" "${INSTALL_PATH}/config/$CONF_FILE" 
cp --update=none "${INSTALL_PATH}/back/$DB_FILE"  "$FILEDB"

echo "[INSTALL] Fixing permissions after copied starter config & DB"

if [ -f "$FILEDB" ]; then
    chown -R www-data:www-data $FILEDB
fi

chmod -R a+rwx $INSTALL_DIR # second time after we copied the files
chmod -R a+rw $INSTALL_PATH/config
chgrp -R www-data  $INSTALL_PATH

# Check if buildtimestamp.txt doesn't exist
if [ ! -f "${INSTALL_PATH}/front/buildtimestamp.txt" ]; then
    # Create buildtimestamp.txt
    date +%s > "${INSTALL_PATH}/front/buildtimestamp.txt"
fi

# start PHP
/etc/init.d/php${PHPVERSION}-fpm start
nginx -t || { echo "[INSTALL] nginx config test failed"; exit 1; }
/etc/init.d/nginx start
#  Activate the virtual python environment
source myenv/bin/activate

echo "[INSTALL] 🚀 Starting app - navigate to your <server IP>:${PORT}"

# Start the NetAlertX python script
# All error and console output being diverted to null,
# otherwise we can get critical errors re I/O
python "$INSTALL_PATH/server/" 2>/dev/null 1>/dev/null &
