#!/bin/bash

echo "---------------------------------------------------------"
echo "[INSTALL]                                    Run start.sh"
echo "---------------------------------------------------------"


INSTALL_DIR=/home/pi  # Specify the installation directory here

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

# Change port number if set
if [ -n "${PORT}" ]; then  
  sed -ie 's/listen 20211/listen '${PORT}'/g' /etc/nginx/sites-available/default
fi 

echo "[INSTALL] Setup NGINX"

# Remove /html folder if exists
sudo rm -R /var/www/html/pialert 

# create symbolic link to the pialert install directory
ln -s $INSTALL_DIR/pialert/front /var/www/html/pialert 
# remove existing pialert site
sudo rm /etc/nginx/conf.d/pialert.conf
# create symbolic link to NGINX configuaration coming with PiAlert
sudo ln -s "$INSTALL_DIR/pialert/install/pialert.conf" /etc/nginx/conf.d/pialert.conf

# Use user-supplied port if set
if [ -n "${PORT}" ]; then  
  sudo sed -i 's/listen 20211/listen '"$PORT"'/g' /etc/nginx/conf.d/pialert.conf
fi

# Change web interface address if set
if [ -n "${LISTEN_ADDR}" ]; then  
  sed -ie 's/listen /listen '${LISTEN_ADDR}:'/g' /etc/nginx/conf.d/pialert.conf
fi

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Define the path to ieee-oui.txt and ieee-iab.txt
oui_file="/usr/share/arp-scan/ieee-oui.txt"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "$oui_file" ]; then
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

# Fixing file permissions
echo "[INSTALL] Fixing file permissions"


chmod -R a+rwx /var/www/html/pialert
chmod -R a+rw $INSTALL_DIR/pialert/front/log
chmod -R a+rwx $INSTALL_DIR

FILEDB=$INSTALL_DIR/pialert/db/pialert.db

if [ -f "$FILEDB" ]; then
    chown -R www-data:www-data $INSTALL_DIR/pialert/db/pialert.db
fi

echo "[INSTALL] Copy starter pialert.db and pialert.conf if they don't exist"

# Copy starter pialert.db and pialert.conf if they don't exist
cp -n "$INSTALL_DIR/pialert/back/pialert.conf" "$INSTALL_DIR/pialert/config/pialert.conf" 
cp -n "$INSTALL_DIR/pialert/back/pialert.db"  "$INSTALL_DIR/pialert/db/pialert.db" 


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

# Start the PiAlert python script
python $INSTALL_DIR/pialert/pialert/
