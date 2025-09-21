#! /bin/bash
# Runtime setup for devcontainer (executed after container starts).
# Prefer building setup into resources/devcontainer-Dockerfile when possible.
# Use this script for runtime-only adjustments (permissions, sockets, ownership,
# and services managed without init) that are difficult at build time.
id

# Define variables (paths, ports, environment)

export APP_DIR="/app"
export APP_COMMAND="/workspaces/NetAlertX/.devcontainer/scripts/restart-backend.sh"
export PHP_FPM_BIN="/usr/sbin/php-fpm83"
export NGINX_BIN="/usr/sbin/nginx"
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
    echo "Setting up ${SOURCE_DIR}..."
    configure_source
    
    echo "--- Starting Development Services ---"
    configure_php


    start_services
}

# safe_link: create a symlink from source to target, removing existing target if necessary
# bypassing the default behavior of symlinking the directory into the target directory if it is a directory
safe_link() {
    # usage: safe_link <source> <target>
    local src="$1"
    local dst="$2"

    # Ensure parent directory exists
    install -d -m 775 "$(dirname "$dst")" >/dev/null 2>&1 || true

    # If target exists, remove it without dereferencing symlinks
    if [ -L "$dst" ] || [ -e "$dst" ]; then
        rm -rf "$dst"
    fi

    # Create link; -n prevents deref, -f replaces if somehow still exists
    ln -sfn "$src" "$dst"
}

# Setup source directory
configure_source() {
    echo "[1/3] Configuring Source..."
    echo "  -> Linking source to ${INSTALL_DIR}"
    echo "Dev">${INSTALL_DIR}/.VERSION
    safe_link ${SOURCE_DIR}/api ${INSTALL_DIR}/api
    safe_link ${SOURCE_DIR}/back ${INSTALL_DIR}/back
    safe_link "${SOURCE_DIR}/config"         "${INSTALL_DIR}/config"
    safe_link "${SOURCE_DIR}/db"         "${INSTALL_DIR}/db"
    if [ ! -f "${SOURCE_DIR}/config/app.conf" ]; then
        cp ${SOURCE_DIR}/back/app.conf ${INSTALL_DIR}/config/
        cp ${SOURCE_DIR}/back/app.db ${INSTALL_DIR}/db/
    fi

    safe_link "${SOURCE_DIR}/docs"       "${INSTALL_DIR}/docs"
    safe_link "${SOURCE_DIR}/front"      "${INSTALL_DIR}/front"
    safe_link "${SOURCE_DIR}/install"    "${INSTALL_DIR}/install"
    safe_link "${SOURCE_DIR}/scripts"    "${INSTALL_DIR}/scripts"
    safe_link "${SOURCE_DIR}/server"     "${INSTALL_DIR}/server"
    safe_link "${SOURCE_DIR}/test"       "${INSTALL_DIR}/test"
    safe_link "${SOURCE_DIR}/mkdocs.yml" "${INSTALL_DIR}/mkdocs.yml"

    echo "  -> Copying static files to ${INSTALL_DIR}"
    cp -R ${SOURCE_DIR}/CODE_OF_CONDUCT.md ${INSTALL_DIR}/
    cp -R ${SOURCE_DIR}/dockerfiles ${INSTALL_DIR}/dockerfiles
    sudo cp -na "${INSTALL_DIR}/back/${CONF_FILE}" "${INSTALL_DIR}/config/${CONF_FILE}"
    sudo cp -na "${INSTALL_DIR}/back/${DB_FILE}" "${FULL_FILEDB_PATH}"
    if [ -e "${INSTALL_DIR}/api/user_notifications.json" ]; then
        echo "  -> Removing existing user_notifications.json"
        sudo rm "${INSTALL_DIR}"/api/user_notifications.json
    fi
    
    echo "  -> Setting ownership and permissions"
    sudo find ${INSTALL_DIR}/ -type d -exec chmod 775 {} \;
    sudo find ${INSTALL_DIR}/ -type f -exec chmod 664 {} \;
    sudo date +%s > "${INSTALL_DIR}/front/buildtimestamp.txt"
    sudo chmod 640 "${INSTALL_DIR}/config/${CONF_FILE}" || true

    echo "  -> Setting up log directory"
    sudo rm -Rf ${INSTALL_DIR}/log
    install -d -o netalertx -g www-data -m 777 ${INSTALL_DIR}/log
    install -d -o netalertx -g www-data -m 777 ${INSTALL_DIR}/log/plugins

    echo "  -> Empty log"|tee ${INSTALL_DIR}/log/app.log \
        ${INSTALL_DIR}/log/app_front.log \
        ${INSTALL_DIR}/log/stdout.log
    touch ${INSTALL_DIR}/log/stderr.log \
    ${INSTALL_DIR}/log/execution_queue.log

    date +%s > /app/front/buildtimestamp.txt

    killall python &>/dev/null
    sleep 1
}

#

# start_services: start crond, PHP-FPM, nginx and the application
start_services() {
    echo "[3/3] Starting services..."

    killall nohup &>/dev/null || true

    killall php-fpm83 &>/dev/null || true
    killall crond &>/dev/null || true
    # Give the OS a moment to release the php-fpm socket
    sleep 0.3
    echo "      -> Starting CronD"
    setsid nohup $CROND_BIN &>/dev/null &

    echo "      -> Starting PHP-FPM"
    setsid nohup $PHP_FPM_BIN &>/dev/null &

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
    setsid nohup $NGINX_BIN &>/dev/null &
    echo "      -> Starting Backend ${APP_DIR}/server..."
    $APP_COMMAND 
    sleep 2
}

# configure_php: configure PHP-FPM and enable dev debug options
configure_php() {
    echo "[2/3] Configuring PHP-FPM..."
    sudo killall php-fpm83 &>/dev/null || true
    install -d -o nginx -g www-data /run/php/ &>/dev/null
    sudo sed -i "/^;pid/c\pid = /run/php/php8.3-fpm.pid" /etc/php83/php-fpm.conf
    sudo sed -i 's|^listen = .*|listen = 127.0.0.1:9000|' /etc/php83/php-fpm.d/www.conf
    sudo sed -i 's|fastcgi_pass .*|fastcgi_pass 127.0.0.1:9000;|' /etc/nginx/http.d/*.conf

    #increase max child process count to 10
    sudo sed -i -e 's/pm.max_children = 5/pm.max_children = 10/' /etc/php83/php-fpm.d/www.conf 

    # find any line in php-fmp that starts with either ;error_log or error_log = and replace it with error_log = /app/log/app.php_errors.log
    sudo sed -i '/^;*error_log\s*=/c\error_log = /app/log/app.php_errors.log' /etc/php83/php-fpm.conf
    # If the line was not found, append it to the end of the file
    if ! grep -q '^error_log\s*=' /etc/php83/php-fpm.conf; then
        echo 'error_log = /app/log/app.php_errors.log' | sudo tee -a /etc/php83/php-fpm.conf
    fi

    sudo mkdir -p /etc/php83/conf.d
    sudo cp /workspaces/NetAlertX/.devcontainer/resources/99-xdebug.ini /etc/php83/conf.d/99-xdebug.ini

    sudo rm -R /var/log/php83 &>/dev/null || true
    install -d -o netalertx -g www-data -m 755 var/log/php83;

    sudo chmod 644 /etc/php83/conf.d/99-xdebug.ini || true

}

# (duplicate start_services removed)



echo "$(git rev-parse --short=8 HEAD)">/app/.VERSION
# Run the main function
main



