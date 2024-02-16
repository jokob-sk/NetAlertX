#!/usr/bin/env bash

echo "---------------------------------------------------------"
echo "[INSTALL]                                    Run start.sh"
echo "---------------------------------------------------------"


INSTALL_DIR=/home/pi  # Specify the installation directory here

# DO NOT CHANGE ANYTHING BELOW THIS LINE!
WEB_UI_DIR=/var/www/html/pialert
NGINX_CONFIG_FILE=/etc/nginx/conf.d/pialert.conf
OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt
FILEDB=$INSTALL_DIR/pialert/db/pialert.db
# DO NOT CHANGE ANYTHING ABOVE THIS LINE!

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then    
  FILECONF=$INSTALL_DIR/pialert/config/pialert.conf 
  if [ -f "$FILECONF" ]; then
    sed -ie "s|Europe/Berlin|${TZ}|g" $INSTALL_DIR/pialert/config/pialert.conf 
  else 
    sed -ie "s|Europe/Berlin|${TZ}|g" $INSTALL_DIR/pialert/back/pialert.conf_bak 
  fi
fi

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi

# Run setup scripts
echo "[INSTALL] Run setup scripts"

"$INSTALL_DIR/pialert/dockerfiles/user-mapping.sh"
"$INSTALL_DIR/pialert/install/install_dependencies.sh" # if modifying this file transfer the chanegs into the root Dockerfile as well!

echo "[INSTALL] Setup NGINX"

# Remove default NGINX site if it is symlinked, or backup it otherwise
if [ -L /etc/nginx/sites-enabled/default ] ; then
  echo "Disabling default NGINX site, removing sym-link in /etc/nginx/sites-enabled"
  sudo rm /etc/nginx/sites-enabled/default
elif [ -f /etc/nginx/sites-enabled/default ]; then
  echo "Disabling default NGINX site, moving config to /etc/nginx/sites-available"
  sudo mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.bkp_pialert
fi

# Clear existing directories and files
if [ -d $WEB_UI_DIR ]; then
  echo "Removing existing PiAlert web-UI"
  sudo rm -R $WEB_UI_DIR
fi

if [ -f $NGINX_CONFIG_FILE ]; then
  echo "Removing existing PiAlert NGINX config"
  sudo rm $NGINX_CONFIG_FILE
fi

# create symbolic link to the pialert install directory
ln -s $INSTALL_DIR/pialert/front $WEB_UI_DIR
# create symbolic link to NGINX configuaration coming with PiAlert
sudo ln -s "$INSTALL_DIR/pialert/install/pialert.conf" /etc/nginx/conf.d/pialert.conf

# Use user-supplied port if set
if [ -n "${PORT}" ]; then
  echo "Setting webserver to user-supplied port ($PORT)"
  sudo sed -i 's/listen 20211/listen '"$PORT"'/g' /etc/nginx/conf.d/pialert.conf
fi

# Change web interface address if set
if [ -n "${LISTEN_ADDR}" ]; then
  echo "Setting webserver to user-supplied address ($LISTEN_ADDR)"
  sed -ie 's/listen /listen '"${LISTEN_ADDR}":'/g' /etc/nginx/conf.d/pialert.conf
fi

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "$OUI_FILE" ]; then
  echo "The file ieee-oui.txt exists. Skipping update_vendors.sh..."
else
  echo "The file ieee-oui.txt does not exist. Running update_vendors..."

  # Run the update_vendors.sh script
  if [ -f "$INSTALL_DIR/pialert/back/update_vendors.sh" ]; then
    "$INSTALL_DIR/pialert/back/update_vendors.sh"
  else
    echo "update_vendors.sh script not found in $INSTALL_DIR."    
  fi
fi

# Create an empty log files

# Create the execution_queue.log file if it doesn't exist
touch "$INSTALL_DIR/pialert/front/log/execution_queue.log"
# Create the pialert_front.log file if it doesn't exist
touch "$INSTALL_DIR/pialert/front/log/pialert_front.log"


# Fixing file permissions
echo "[INSTALL] Fixing file permissions"

echo "[INSTALL] Fixing WEB_UI_DIR: $WEB_UI_DIR"

chmod -R a+rwx $WEB_UI_DIR

echo "[INSTALL] Fixing INSTALL_DIR: $INSTALL_DIR"

chmod -R a+rw $INSTALL_DIR/pialert/front/log
chmod -R a+rwx $INSTALL_DIR

echo "[INSTALL] Copy starter pialert.db and pialert.conf if they don't exist"

# DANGER ZONE: ALWAYS_FRESH_INSTALL 
if [ "$ALWAYS_FRESH_INSTALL" = true ]; then
  echo "[INSTALL] ❗ ALERT db and config folders are cleared because the ALWAYS_FRESH_INSTALL is set to: $ALWAYS_FRESH_INSTALL❗"
  # Delete content of "$INSTALL_DIR/pialert/config/"
  rm -rf "$INSTALL_DIR/pialert/config/"*
  
  # Delete content of "$FILEDB"
  rm -rf "$FILEDB"/*
fi


# Copy starter pialert.db and pialert.conf if they don't exist
cp -n "$INSTALL_DIR/pialert/back/pialert.conf" "$INSTALL_DIR/pialert/config/pialert.conf" 
cp -n "$INSTALL_DIR/pialert/back/pialert.db"  "$FILEDB"

echo "[INSTALL] Fixing permissions after copied starter config & DB"

if [ -f "$FILEDB" ]; then
    chown -R www-data:www-data $FILEDB
fi

chmod -R a+rwx $INSTALL_DIR # second time after we copied the files
chmod -R a+rw $INSTALL_DIR/pialert/config
sudo chgrp -R www-data  $INSTALL_DIR/pialert

# Check if buildtimestamp.txt doesn't exist
if [ ! -f "$INSTALL_DIR/pialert/front/buildtimestamp.txt" ]; then
    # Create buildtimestamp.txt
    date +%s > "$INSTALL_DIR/pialert/front/buildtimestamp.txt"
fi

# start PHP
/etc/init.d/php8.2-fpm start
/etc/init.d/nginx start

# Start Nginx and your application to start at boot (if needed)
# systemctl start nginx
# systemctl enable nginx

# # systemctl enable pi-alert
# sudo systemctl restart nginx

#  Activate the virtual python environment
source myenv/bin/activate

echo "[INSTALL] 🚀 Starting app - navigate to your <server IP>:$PORT"

# Start the PiAlert python script
python $INSTALL_DIR/pialert/pialert/
