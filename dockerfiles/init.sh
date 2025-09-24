#!/usr/bin/with-contenv bash

echo "---------------------------------------------------------
[INSTALL]                                    Run init.sh
---------------------------------------------------------"

DEFAULT_PUID=102
DEFAULT_GID=82

PUID=${PUID:-${DEFAULT_PUID}}
PGID=${PGID:-${DEFAULT_GID}}

echo "[INSTALL] Setting up user UID and GID"

groupmod -o -g "$PGID" www-data 2>/dev/null || echo "Failed to set user GID to ${PGID}, using existing GID"
usermod -o -u "$PUID" nginx 2>/dev/null || echo "Failed to set user UID to ${PUID}, using existing UID"

echo "
---------------------------------------------------------
GID/UID
---------------------------------------------------------
User UID:    $(id -u nginx)
User GID:    $(getent group www-data | cut -d: -f3)
---------------------------------------------------------"

# DO NOT CHANGE ANYTHING BELOW THIS LINE!

CONF_FILE="app.conf"
DB_FILE="app.db"
FULL_FILEDB_PATH="${NETALERTX_DB}/${DB_FILE}"
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

  # Delete content of "$NETALERTX_CONFIG/"
  rm -rf ${NETALERTX_CONFIG}/*

  # Delete content of "$NETALERTX_DB/"
  rm -rf ${NETALERTX_DB}/*
fi

# OVERRIDE settings: Handling APP_CONF_OVERRIDE
# Check if APP_CONF_OVERRIDE is set

# remove old
rm -f "${NETALERTX_CONFIG}/app_conf_override.json"

if [ -z "$APP_CONF_OVERRIDE" ]; then
  echo "APP_CONF_OVERRIDE is not set. Skipping config file creation."
else
  # Save the APP_CONF_OVERRIDE env variable as a JSON file
  echo "$APP_CONF_OVERRIDE" > "${NETALERTX_CONFIG}/app_conf_override.json"
  echo "Config file saved to ${NETALERTX_CONFIG}/app_conf_override.json"
fi

# 🔻 FOR BACKWARD COMPATIBILITY - REMOVE AFTER 12/12/2025

# Check if pialert.db exists, then create a symbolic link to app.db
if [ -f "${INSTALL_DIR_OLD}/db/${OLD_APP_NAME}.db" ]; then
    ln -sf "${INSTALL_DIR_OLD}/db/${OLD_APP_NAME}.db" "${FULL_FILEDB_PATH}"
fi

# Check if ${OLD_APP_NAME}.conf exists, then create a symbolic link to app.conf
if [ -f "${INSTALL_DIR_OLD}/config/${OLD_APP_NAME}.conf" ]; then
    ln -sf "${INSTALL_DIR_OLD}/config/${OLD_APP_NAME}.conf" "${NETALERTX_CONFIG}/${CONF_FILE}"
fi
# 🔺 FOR BACKWARD COMPATIBILITY - REMOVE AFTER 12/12/2025

echo "[INSTALL] Copy starter ${DB_FILE} and ${CONF_FILE} if they don't exist"

# Copy starter app.db, app.conf if they don't exist
cp -n "${NETALERTX_BACK}/${CONF_FILE}" "${NETALERTX_CONFIG}/${CONF_FILE}" 2>/dev/null || true
cp -n "${NETALERTX_BACK}/${DB_FILE}" "${FULL_FILEDB_PATH}" 2>/dev/null || true

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then
  FILECONF="${NETALERTX_CONFIG}/${CONF_FILE}"
  echo "[INSTALL] Setup timezone"
  sed -i "\#^TIMEZONE=#c\TIMEZONE='${TZ}'" "${FILECONF}"

  # set TimeZone in container
  cp /usr/share/zoneinfo/$TZ /etc/localtime
  echo $TZ > /etc/timezone
fi

# if custom variables not set we do not need to do anything
if [ -n "${LOADED_PLUGINS}" ]; then
  FILECONF="${NETALERTX_CONFIG}/${CONF_FILE}"
  echo "[INSTALL] Setup custom LOADED_PLUGINS variable"
  sed -i "\#^LOADED_PLUGINS=#c\LOADED_PLUGINS=${LOADED_PLUGINS}" "${FILECONF}"
fi

echo "[INSTALL] Setup NGINX"
echo "Setting webserver to address ($LISTEN_ADDR) and port ($PORT)"
envsubst '$NETALERTX_APP $LISTEN_ADDR $PORT' < "${NETALERTX_APP}/install/netalertx.template.conf" > "${NGINX_CONFIG_FILE}"

# Run the hardware vendors update at least once
echo "[INSTALL] Run the hardware vendors update"

# Check if ieee-oui.txt or ieee-iab.txt exist
if [ -f "${OUI_FILE}" ]; then
  echo "The file ieee-oui.txt exists. Skipping update_vendors.sh..."
else
  echo "The file ieee-oui.txt does not exist. Running update_vendors..."

  # Run the update_vendors.sh script
  if [ -f "${NETALERTX_BACK}/update_vendors.sh" ]; then
    "${NETALERTX_BACK}/update_vendors.sh"
  else
    echo "update_vendors.sh script not found in ${NETALERTX_APP}."
  fi
fi

echo "[INSTALL] Fixing permissions after runtime initialization"
chown -R nginx:www-data "${NETALERTX_CONFIG}" "${NETALERTX_DB}" "${NETALERTX_LOG}"

echo -e "
            [ENV] PATH                      is ${PATH}
            [ENV] PORT                      is ${PORT}
            [ENV] TZ                        is ${TZ}
            [ENV] LISTEN_ADDR               is ${LISTEN_ADDR}
            [ENV] ALWAYS_FRESH_INSTALL      is ${ALWAYS_FRESH_INSTALL}
        "
