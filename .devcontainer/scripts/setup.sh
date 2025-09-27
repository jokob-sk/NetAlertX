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
export NGINX_BIN="/workspaces/NetAlertX/.devcontainer/scripts/start-nginx.sh"
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
    sudo chown $(id -u):$(id -g) /workspaces
    sudo chown 755 /workspaces
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
    sudo umount "${INSTALL_DIR}/log" 2>/dev/null
    sudo umount "${INSTALL_DIR}/api" 2>/dev/null
    sudo rm -Rf ${INSTALL_DIR} || true
    sudo ln -s ${SOURCE_DIR} ${INSTALL_DIR}
    
    echo "  -> Mounting ramdisks for /log and /api"
    sudo mkdir -p /tmp/log /tmp/api || true
    sudo cp -R ${SOURCE_DIR}/log/ /tmp/log/ || true
    sudo cp -R ${SOURCE_DIR}/api/ /tmp/api/ || true
    sudo mkdir -p ${NETALERTX_API} ${NETALERTX_LOG}
    # mount tmpfs with netalertx:netalertx ownership and 775 permissions
    sudo mount -o uid=$(id -u netalertx),gid=$(id -g netalertx),mode=775 -t tmpfs -o size=256M tmpfs "${NETALERTX_LOG}"
    sudo mount -o uid=$(id -u netalertx),gid=$(id -g netalertx),mode=775 -t tmpfs -o size=256M tmpfs "${NETALERTX_API}"
    # mount tmpfs with root:root ownership and 755 permissions
    sudo cp -R /tmp/log/* ${NETALERTX_LOG} 2>/dev/null || true
    sudo cp -R /tmp/api/* ${NETALERTX_API} 2>/dev/null || true
    sudo rm -Rf /tmp/log /tmp/api || true 
    echo "Dev">${INSTALL_DIR}/.VERSION
    


    
    echo "  -> Setting ownership and permissions"
    chmod +x /workspaces/NetAlertX/.devcontainer/scripts/start-nginx.sh
    sudo date +%s > "${INSTALL_DIR}/front/buildtimestamp.txt"
    


    echo "  -> Empty log"|tee ${INSTALL_DIR}/log/app.log \
        ${INSTALL_DIR}/log/app_front.log \
        ${INSTALL_DIR}/log/stdout.log
    touch ${INSTALL_DIR}/log/stderr.log \
    ${INSTALL_DIR}/log/execution_queue.log
    echo 0>${INSTALL_DIR}/log/db_is_locked.log
    mkdir -p /app/log/plugins
    sudo chown -R netalertx:www-data ${INSTALL_DIR}

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
    install -d -o netalertx -g www-data /run/php/ &>/dev/null
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
    sudo install -d -o netalertx -g www-data -m 775 /run/php

    sudo rm /var/lib/nginx/logs/ && sudo install -d -o netalertx -g www-data /var/lib/nginx/logs/
    sudo rm /var/log/nginx && sudo install -d -o netalertx -g www-data /var/log/nginx
    sudo chown -R netalertx:www-data /var/log/nginx
    sudo chown -R netalertx:www-data /run/nginx

}

# (duplicate start_services removed)



echo "$(git rev-parse --short=8 HEAD)">/app/.VERSION
# Run the main function
main



