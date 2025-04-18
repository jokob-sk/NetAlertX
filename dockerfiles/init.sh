#!/usr/bin/with-contenv bash

echo "---------------------------------------------------------
[INSTALL]                                    Run init.sh
---------------------------------------------------------"

DEFAULT_PUID=102
DEFAULT_GID=82

PUID=${PUID:-${DEFAULT_PUID}}
PGID=${PGID:-${DEFAULT_GID}}

echo "[INSTALL] Setting up user UID and GID"

if ! groupmod -o -g "$PGID" www-data && [ "$PGID" != "$DEFAULT_GID" ] ; then
   echo "Failed to set user GID to ${PGID}, trying with default GID ${DEFAULT_GID}"
   groupmod -o -g "$DEFAULT_GID" www-data
fi
if ! usermod -o -u "$PUID" nginx && [ "$PUID" != "$DEFAULT_PUID" ] ; then
   echo "Failed to set user UID to ${PUID}, trying with default PUID ${DEFAULT_PUID}"
   usermod -o -u "$DEFAULT_PUID" nginx
fi

echo "
---------------------------------------------------------
GID/UID
---------------------------------------------------------
User UID:    $(id -u nginx)
User GID:    $(getent group www-data | cut -d: -f3)
---------------------------------------------------------"

chown nginx:nginx /run/nginx/ /var/log/nginx/ /var/lib/nginx/ /var/lib/nginx/tmp/
chgrp www-data /var/www/localhost/htdocs/

export INSTALL_DIR=/app  # Specify the installation directory here

# DO NOT CHANGE ANYTHING BELOW THIS LINE!

CONF_FILE="app.conf"
NGINX_CONF_FILE=netalertx.conf
DB_FILE="app.db"
FULL_FILEDB_PATH="${INSTALL_DIR}/db/${DB_FILE}"
NGINX_CONFIG_FILE="/etc/nginx/http.d/${NGINX_CONF_FILE}"
OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt

INSTALL_DIR_OLD=/home/pi/pialert
OLD_APP_NAME=pialert

# DO NOT CHANGE ANYTHING ABOVE THIS LINE!

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'."
    exit 1
fi

# DANGER ZONE: ALWAYS_FRESH_INSTALL
if [ "$ALWAYS_FRESH_INSTALL" = true ]; then
  echo "[INSTALL] ❗ ALERT /db and /config folders are cleared because the ALWAYS_FRESH_INSTALL is set to: $ALWAYS_FRESH_INSTALL❗"

  # Delete content of "$INSTALL_DIR/config/"
  rm -rf "$INSTALL_DIR/config/"*
  rm -rf "$INSTALL_DIR_OLD/config/"*

  # Delete content of "$INSTALL_DIR/db/"
  rm -rf "$INSTALL_DIR/db/"*
  rm -rf "$INSTALL_DIR_OLD/db/"*
fi

# OVERRIDE settings: Handling APP_CONF_OVERRIDE
# Check if APP_CONF_OVERRIDE is set

# remove old
rm "${INSTALL_DIR}/config/app_conf_override.json"

if [ -z "$APP_CONF_OVERRIDE" ]; then
  echo "APP_CONF_OVERRIDE is not set. Skipping config file creation."
else
  # Save the APP_CONF_OVERRIDE env variable as a JSON file
  echo "$APP_CONF_OVERRIDE" > "${INSTALL_DIR}/config/app_conf_override.json"
  echo "Config file saved to ${INSTALL_DIR}/config/app_conf_override.json"
fi

# 🔻 FOR BACKWARD COMPATIBILITY - REMOVE AFTER 12/12/2025

# Check if pialert.db exists, then create a symbolic link to app.db
if [ -f "${INSTALL_DIR_OLD}/db/${OLD_APP_NAME}.db" ]; then
    ln -s "${INSTALL_DIR_OLD}/db/${OLD_APP_NAME}.db" "${FULL_FILEDB_PATH}"
fi

# Check if ${OLD_APP_NAME}.conf exists, then create a symbolic link to app.conf
if [ -f "${INSTALL_DIR_OLD}/config/${OLD_APP_NAME}.conf" ]; then
    ln -s "${INSTALL_DIR_OLD}/config/${OLD_APP_NAME}.conf" "${INSTALL_DIR}/config/${CONF_FILE}"
fi
# 🔺 FOR BACKWARD COMPATIBILITY - REMOVE AFTER 12/12/2025

echo "[INSTALL] Copy starter ${DB_FILE} and ${CONF_FILE} if they don't exist"

# Copy starter app.db, app.conf if they don't exist
cp -na "${INSTALL_DIR}/back/${CONF_FILE}" "${INSTALL_DIR}/config/${CONF_FILE}"
cp -na "${INSTALL_DIR}/back/${DB_FILE}" "${FULL_FILEDB_PATH}"

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then
  FILECONF="${INSTALL_DIR}/config/${CONF_FILE}"
  echo "[INSTALL] Setup timezone"
  sed -i "\#^TIMEZONE=#c\TIMEZONE='${TZ}'" "${FILECONF}"

  # set TimeZone in container
  cp /usr/share/zoneinfo/$TZ /etc/localtime
  echo $TZ > /etc/timezone
fi

# if custom variables not set we do not need to do anything
if [ -n "${LOADED_PLUGINS}" ]; then
  FILECONF="${INSTALL_DIR}/config/${CONF_FILE}"
  echo "[INSTALL] Setup custom LOADED_PLUGINS variable"
  sed -i "\#^LOADED_PLUGINS=#c\LOADED_PLUGINS=${LOADED_PLUGINS}" "${FILECONF}"
fi

echo "[INSTALL] Setup NGINX"
echo "Setting webserver to address ($LISTEN_ADDR) and port ($PORT)"
envsubst '$INSTALL_DIR $LISTEN_ADDR $PORT' < "${INSTALL_DIR}/install/netalertx.template.conf" > "${NGINX_CONFIG_FILE}"

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "${OUI_FILE}" ]; then
  echo "The file ieee-oui.txt exists. Skipping update_vendors.sh..."
else
  echo "The file ieee-oui.txt does not exist. Running update_vendors..."

  # Run the update_vendors.sh script
  if [ -f "${INSTALL_DIR}/back/update_vendors.sh" ]; then
    "${INSTALL_DIR}/back/update_vendors.sh"
  else
    echo "update_vendors.sh script not found in ${INSTALL_DIR}."
  fi
fi

# Create an empty log files
# Create the execution_queue.log and app_front.log files if they don't exist
touch "${INSTALL_DIR}"/log/{app.log,execution_queue.log,app_front.log,app.php_errors.log,stderr.log,stdout.log,db_is_locked.log}
touch "${INSTALL_DIR}"/api/user_notifications.json

# Create plugins sub-directory if it doesn't exist in case a custom log folder is used
mkdir -p "${INSTALL_DIR}"/log/plugins

echo "[INSTALL] Fixing permissions after copied starter config & DB"
chown -R nginx:www-data "${INSTALL_DIR}"

chmod 750 "${INSTALL_DIR}"/{config,log,db}
find "${INSTALL_DIR}"/{config,log,db} -type f -exec chmod 640 {} \;

# Check if buildtimestamp.txt doesn't exist
if [ ! -f "${INSTALL_DIR}/front/buildtimestamp.txt" ]; then
    # Create buildtimestamp.txt
    date +%s > "${INSTALL_DIR}/front/buildtimestamp.txt"
    chown nginx:www-data "${INSTALL_DIR}/front/buildtimestamp.txt"
fi

echo -e "
            [ENV] PATH                      is ${PATH}
            [ENV] PORT                      is ${PORT}
            [ENV] TZ                        is ${TZ}
            [ENV] LISTEN_ADDR               is ${LISTEN_ADDR}
            [ENV] ALWAYS_FRESH_INSTALL      is ${ALWAYS_FRESH_INSTALL}
        "
