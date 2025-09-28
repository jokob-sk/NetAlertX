#! /bin/sh
# Runtime setup for devcontainer (executed after container starts).
# Prefer building setup into resources/devcontainer-Dockerfile when possible.
# Use this script for runtime-only adjustments (permissions, sockets, ownership,
# and services managed without init) that are difficult at build time.
id

# Define variables (paths, ports, environment)

export APP_DIR="/app"
export APP_COMMAND="/workspaces/NetAlertX/.devcontainer/scripts/restart-backend.sh"
export PHP_FPM_BIN="/usr/sbin/php-fpm83"
export CROND_BIN="/usr/sbin/crond -f"


export ALWAYS_FRESH_INSTALL=false
export INSTALL_DIR=/app
export APP_DATA_LOCATION=/app/config
export APP_CONFIG_LOCATION=/app/config
export LOGS_LOCATION=/app/logs
export CONF_FILE="app.conf"
export NGINX_CONF_FILE=netalertx.conf
export DB_FILE="app.db"
export FULL_FILEDB_PATH="${INSTALL_DIR}/db/${DB_FILE}"
export NGINX_CONFIG_FILE="/etc/nginx/http.d/${NGINX_CONF_FILE}"
export OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt
export TZ=Europe/Paris
export PORT=20211
export SOURCE_DIR="/workspaces/NetAlertX"


main() {
    echo "=== NetAlertX Development Container Setup ==="
    killall php-fpm83 nginx crond python3 2>/dev/null
    
    echo "Setting up ${SOURCE_DIR}..."
    sudo chown $(id -u):$(id -g) /workspaces
    sudo chown 755 /workspaces
    configure_source
    
    echo "--- Starting Development Services ---"
    configure_php


    start_services
}

isRamDisk() {
  if [ -z "$1" ] || [ ! -d "$1" ]; then
    echo "Usage: isRamDisk <directory>" >&2
    return 2
  fi

  local fstype
  fstype=$(df -T "$1" | awk 'NR==2 {print $2}')

  if [[ "$fstype" == "tmpfs" || "$fstype" == "ramfs" ]]; then
    return 0 # Success (is a ramdisk)
  else
    return 1 # Failure (is not a ramdisk)
  fi
}

# Setup source directory
configure_source() {
    echo "[1/3] Configuring Source..."
    echo "  -> Cleaning up previous instances"
    isRamDisk ${NETALERTX_LOG} && sudo umount "${NETALERTX_LOG}"
    isRamDisk ${NETALERTX_API} && sudo umount "${NETALERTX_API}"
    sleep 1
    sudo rm -Rf ${NETALERTX_APP}/ 

    echo "  -> Linking source to ${NETALERTX_APP}"
    sudo ln -s ${SOURCE_DIR}/ ${NETALERTX_APP}
    
    echo "  -> Mounting ramdisks for /log and /api"
    mkdir -p ${NETALERTX_LOG} ${NETALERTX_API}
    sudo mount -o uid=$(id -u netalertx),gid=$(id -g netalertx),mode=775 -t tmpfs -o size=256M tmpfs "${NETALERTX_LOG}"
    sudo mount -o uid=$(id -u netalertx),gid=$(id -g netalertx),mode=775 -t tmpfs -o size=256M tmpfs "${NETALERTX_API}"
    mkdir -p ${NETALERTX_PLUGINS_LOG}
    touch ${NETALERTX_PLUGINS_LOG}/.git-placeholder ${NETALERTX_API}/.git-placeholder
    # mount tmpfs with root:root ownership and 755 permissions


    echo "  -> Empty log"|tee ${INSTALL_DIR}/log/app.log \
        ${INSTALL_DIR}/log/app_front.log \
        ${INSTALL_DIR}/log/stdout.log
    touch ${INSTALL_DIR}/log/stderr.log \
        ${INSTALL_DIR}/log/execution_queue.log
    echo 0>${INSTALL_DIR}/log/db_is_locked.log
    mkdir -p /app/log/plugins
    sudo chown -R netalertx:www-data ${INSTALL_DIR}

    

    killall python &>/dev/null
    sleep 1
}

# configure_php: configure PHP-FPM and enable dev debug options
configure_php() {
    echo "[2/3] Configuring PHP-FPM..."
    sudo chown netalertx:netalertx /run/php/ 2>/dev/null || true

    sudo cp /workspaces/NetAlertX/.devcontainer/resources/99-xdebug.ini ${SYSTEM_SERVICES_PHP_FPM_D}/99-xdebug.ini

}

# start_services: start crond, PHP-FPM, nginx and the application
start_services() {
    echo "[3/3] Starting services..."

    echo "      -> Starting CronD"
    setsid nohup /services/start-crond.sh &>/dev/null &

    echo "      -> Starting PHP-FPM"
    setsid nohup services/start-php-fpm.sh &>/dev/null &

    sudo killall nginx &>/dev/null || true
    # Wait for the previous nginx processes to exit and for the port to free up
    tries=0
    while ss -ltn | grep -q ":${PORT}[[:space:]]" && [ $tries -lt 10 ]; do
        echo "  -> Waiting for port ${PORT} to free..."
        sleep 0.2
        tries=$((tries+1))
    done
    sleep 0.2
    echo "      -> Starting Nginx"
    setsid nohup /services/start-nginx.sh &>/dev/null &
    echo "      -> Starting Backend ${APP_DIR}/server..."
    /services/start-backend.sh 
    sleep 2
}



echo "$(git rev-parse --short=8 HEAD)">/app/.VERSION
# Run the main function
main



