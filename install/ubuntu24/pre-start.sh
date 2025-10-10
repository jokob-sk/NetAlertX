#!/usr/bin/env sh

# 🛑 Important: This is only used for the bare-metal install 🛑 

# DO NOT CHANGE ANYTHING BELOW THIS LINE!
INSTALL_DIR=/app
INSTALL_SYSTEM_NAME=ubuntu24
INSTALLER_DIR=${INSTALL_DIR}/install/$INSTALL_SYSTEM_NAME
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# DO NOT CHANGE ANYTHING ABOVE THIS LINE!

# unmounting in case already mounted
umount "${INSTALL_DIR}/log" 2>/dev/null
umount "${INSTALL_DIR}/api" 2>/dev/null

rm -R "${INSTALL_DIR}/log/*" "${INSTALL_DIR}/api/*" 2>/dev/null

mkdir -p "${INSTALL_DIR}/log" "${INSTALL_DIR}/api"

mount -t tmpfs -o noexec,nosuid,nodev tmpfs "${INSTALL_DIR}/log"
mount -t tmpfs -o noexec,nosuid,nodev tmpfs "${INSTALL_DIR}/api"


# Create log files if they don't exist
touch "${INSTALL_DIR}"/log/{app.log,execution_queue.log,app_front.log,app.php_errors.log,stderr.log,stdout.log,db_is_locked.log}
touch "${INSTALL_DIR}"/api/user_notifications.json
# Create plugins sub-directory if it doesn't exist in case a custom log folder is used
mkdir -p "${INSTALL_DIR}"/log/plugins


chgrp -R www-data "${INSTALL_DIR}/log" "${INSTALL_DIR}/api"
chmod -R u+rwx,g+rwx,o=rx "${INSTALL_DIR}/api"
chmod -R u+rwX,g+rwX,o=rX "${INSTALL_DIR}/log"
