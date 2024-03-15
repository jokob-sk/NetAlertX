#!/usr/bin/with-contenv bash

echo "---------------------------------------------------------"
echo "[INSTALL]                                    Run setup.sh"
echo "---------------------------------------------------------"

export INSTALL_DIR=/home/pi  # Specify the installation directory here

# DO NOT CHANGE ANYTHING BELOW THIS LINE!
NGINX_CONFIG_FILE=/etc/nginx/http.d/pialert.conf
OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt
FILEDB="${INSTALL_DIR}/pialert/db/pialert.db"
# DO NOT CHANGE ANYTHING ABOVE THIS LINE!

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'."
    exit 1
fi

echo "[INSTALL] Copy starter pialert.db and pialert.conf if they don't exist"

# DANGER ZONE: ALWAYS_FRESH_INSTALL 
if [ "$ALWAYS_FRESH_INSTALL" = true ]; then
  echo "[INSTALL] ❗ ALERT /db and /config folders are cleared because the ALWAYS_FRESH_INSTALL is set to: $ALWAYS_FRESH_INSTALL❗"
  # Delete content of "$INSTALL_DIR/pialert/config/"
  rm -rf "$INSTALL_DIR/pialert/config/"*
  
  # Delete content of "$INSTALL_DIR/pialert/db/"
  rm -rf "$INSTALL_DIR/pialert/db/"*
fi

# Copy starter pialert.db and pialert.conf if they don't exist
cp -na "${INSTALL_DIR}/pialert/back/pialert.conf" "${INSTALL_DIR}/pialert/config/pialert.conf"
cp -na "${INSTALL_DIR}/pialert/back/pialert.db" "${FILEDB}"

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then
  FILECONF="${INSTALL_DIR}/pialert/config/pialert.conf"
  echo "[INSTALL] Setup timezone"
  sed -i "\#^TIMEZONE=#c\TIMEZONE='${TZ}'" "${FILECONF}"
fi

echo "[INSTALL] Setup NGINX"
echo "Setting webserver to address ($LISTEN_ADDR) and port ($PORT)"
envsubst '$INSTALL_DIR $LISTEN_ADDR $PORT' < "${INSTALL_DIR}/pialert/install/pialert.template.conf" > "${NGINX_CONFIG_FILE}"

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "${OUI_FILE}" ]; then
  echo "The file ieee-oui.txt exists. Skipping update_vendors.sh..."
else
  echo "The file ieee-oui.txt does not exist. Running update_vendors..."

  # Run the update_vendors.sh script
  if [ -f "${INSTALL_DIR}/pialert/back/update_vendors.sh" ]; then
    "${INSTALL_DIR}/pialert/back/update_vendors.sh"
  else
    echo "update_vendors.sh script not found in ${INSTALL_DIR}."
  fi
fi

# Create an empty log files
# Create the execution_queue.log and pialert_front.log files if they don't exist
touch "${INSTALL_DIR}"/pialert/front/log/{execution_queue.log,pialert_front.log,pialert.php_errors.log,stderr.log,stdout.log}

echo "[INSTALL] Fixing permissions after copied starter config & DB"
chown -R nginx:www-data "${INSTALL_DIR}"/pialert/{config,front/log,db}
chmod 750 "${INSTALL_DIR}"/pialert/{config,front/log,db}
chmod 640 "${INSTALL_DIR}"/pialert/{config,front/log,db}/*

# Check if buildtimestamp.txt doesn't exist
if [ ! -f "${INSTALL_DIR}/pialert/front/buildtimestamp.txt" ]; then
    # Create buildtimestamp.txt
    date +%s > "${INSTALL_DIR}/pialert/front/buildtimestamp.txt"
    chown nginx:www-data "${INSTALL_DIR}/pialert/front/buildtimestamp.txt"
fi
