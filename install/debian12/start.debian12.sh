#!/usr/bin/env bash

echo "---------------------------------------------------------"
echo "[INSTALL]                           Run start.debian12.sh"
echo "---------------------------------------------------------"
echo
echo "This script will set up and start NetAlertX on your Debian12 system."

INSTALL_DIR=/app  # Specify the installation directory here

# DO NOT CHANGE ANYTHING BELOW THIS LINE!
INSTALLER_DIR=$INSTALL_DIR/install/debian12
CONF_FILE=app.conf
DB_FILE=app.db
NGINX_CONF_FILE=netalertx.conf
WEB_UI_DIR=/var/www/html/netalertx
NGINX_CONFIG_FILE=/etc/nginx/conf.d/$NGINX_CONF_FILE
OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt
INSTALL_PATH=$INSTALL_DIR/
FILEDB=$INSTALL_PATH/db/$DB_FILE
# DO NOT CHANGE ANYTHING ABOVE THIS LINE!

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then    
  FILECONF=$INSTALL_PATH/config/$CONF_FILE 
  if [ -f "$FILECONF" ]; then
    sed -ie "s|Europe/Berlin|${TZ}|g" $INSTALL_PATH/config/$CONF_FILE 
  else 
    sed -ie "s|Europe/Berlin|${TZ}|g" $INSTALL_PATH/back/$CONF_FILE.bak 
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


"${INSTALLER_DIR}/install_dependencies.debian12.sh" # if modifying this file transfer the changes into the root Dockerfile.debian as well!


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
  echo "Disabling default NGINX site, removing sym-link in /etc/nginx/sites-enabled"
  sudo rm /etc/nginx/sites-enabled/default
elif [ -f /etc/nginx/sites-enabled/default ]; then
  echo "Disabling default NGINX site, moving config to /etc/nginx/sites-available"
  sudo mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.bkp_netalertx
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
sudo ln -s "${INSTALL_PATH}/install/debian12/netalertx.conf" /etc/nginx/conf.d/$NGINX_CONF_FILE

# Use user-supplied port if set
if [ -n "${PORT}" ]; then
  echo "Setting webserver to user-supplied port ($PORT)"
  sudo sed -i 's/listen 20211/listen '"$PORT"'/g' /etc/nginx/conf.d/$NGINX_CONF_FILE
fi

# Change web interface address if set
if [ -n "${LISTEN_ADDR}" ]; then
  echo "Setting webserver to user-supplied address (${LISTEN_ADDR})"
  sed -ie 's/listen /listen '"${LISTEN_ADDR}":'/g' /etc/nginx/conf.d/$NGINX_CONF_FILE
fi

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "$OUI_FILE" ]; then
  echo "The file ieee-oui.txt exists. Skipping update_vendors.sh..."
else
  echo "The file ieee-oui.txt does not exist. Running update_vendors..."

  # Run the update_vendors.sh script
  if [ -f "${INSTALL_PATH}/back/update_vendors.sh" ]; then
    "${INSTALL_PATH}/back/update_vendors.sh"
  else
    echo "update_vendors.sh script not found in $INSTALL_DIR."    
  fi
fi

# Create an empty log files

# Create the execution_queue.log file if it doesn't exist
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
cp -n "${INSTALL_PATH}/back/$CONF_FILE" "${INSTALL_PATH}/config/$CONF_FILE" 
cp -n "${INSTALL_PATH}/back/$DB_FILE"  "$FILEDB"

echo "[INSTALL] Fixing permissions after copied starter config & DB"

if [ -f "$FILEDB" ]; then
    chown -R www-data:www-data $FILEDB
fi

chmod -R a+rwx $INSTALL_DIR # second time after we copied the files
chmod -R a+rw $INSTALL_PATH/config
sudo chgrp -R www-data  $INSTALL_PATH

# Check if buildtimestamp.txt doesn't exist
if [ ! -f "${INSTALL_PATH}/front/buildtimestamp.txt" ]; then
    # Create buildtimestamp.txt
    date +%s > "${INSTALL_PATH}/front/buildtimestamp.txt"
fi

# start PHP
/etc/init.d/php8.2-fpm start
nginx -t || { echo "[INSTALL] nginx config test failed"; exit 1; }
/etc/init.d/nginx start

# Start Nginx and your application to start at boot (if needed)
# systemctl start nginx
# systemctl enable nginx

# # systemctl enable pi-alert
# sudo systemctl restart nginx

#  Activate the virtual python environment
source myenv/bin/activate

echo "[INSTALL] 🚀 Starting app - navigate to your <server IP>:${PORT}"

# Start the NetAlertX python script
python $INSTALL_PATH/server/
