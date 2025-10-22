#!/bin/bash
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
export LOGS_LOCATION=/app/logs
export CONF_FILE="app.conf"
export DB_FILE="app.db"
export FULL_FILEDB_PATH="${INSTALL_DIR}/db/${DB_FILE}"
export OUI_FILE="/usr/share/arp-scan/ieee-oui.txt" # Define the path to ieee-oui.txt and ieee-iab.txt
export TZ=Europe/Paris
export PORT=20211
export SOURCE_DIR="/workspaces/NetAlertX"


ensure_docker_socket_access() {
  local socket="/var/run/docker.sock"
  if [ ! -S "${socket}" ]; then
    echo "docker socket not present; skipping docker group configuration"
    return
  fi

  local sock_gid
  sock_gid=$(stat -c '%g' "${socket}" 2>/dev/null || true)
  if [ -z "${sock_gid}" ]; then
    echo "unable to determine docker socket gid; skipping docker group configuration"
    return
  fi

  local group_entry=""
  if command -v getent >/dev/null 2>&1; then
    group_entry=$(getent group "${sock_gid}" 2>/dev/null || true)
  else
    group_entry=$(grep -E ":${sock_gid}:" /etc/group 2>/dev/null || true)
  fi

  local group_name=""
  if [ -n "${group_entry}" ]; then
    group_name=$(echo "${group_entry}" | cut -d: -f1)
  else
    group_name="docker-host"
    sudo addgroup -g "${sock_gid}" "${group_name}" 2>/dev/null || group_name=$(grep -E ":${sock_gid}:" /etc/group | head -n1 | cut -d: -f1)
  fi

  if [ -z "${group_name}" ]; then
    echo "failed to resolve group for docker socket gid ${sock_gid}; skipping docker group configuration"
    return
  fi

  if ! id -nG netalertx | tr ' ' '\n' | grep -qx "${group_name}"; then
    sudo addgroup netalertx "${group_name}" 2>/dev/null || true
  fi
}


main() {
    echo "=== NetAlertX Development Container Setup ==="
    killall php-fpm83 nginx crond python3 2>/dev/null
    sleep 1
    echo "Setting up ${SOURCE_DIR}..."
    ensure_docker_socket_access
    sudo chown $(id -u):$(id -g) /workspaces
    sudo chmod 755 /workspaces
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

  if [ "$fstype" = "tmpfs" ] || [ "$fstype" = "ramfs" ]; then
    return 0 # Success (is a ramdisk)
  else
    return 1 # Failure (is not a ramdisk)
  fi
}

# Setup source directory
configure_source() {
    echo "[1/4] Configuring System..."
    echo "      -> Setting up /services permissions"
    sudo chown -R netalertx /services

    echo "[2/4] Configuring Source..."
    echo "      -> Cleaning up previous instances"

    test -e ${NETALERTX_LOG} && sudo umount "${NETALERTX_LOG}" 2>/dev/null || true
    test -e ${NETALERTX_API} && sudo umount "${NETALERTX_API}" 2>/dev/null || true
    test -e ${NETALERTX_APP} && sudo rm -Rf ${NETALERTX_APP}/

    echo "      -> Linking source to ${NETALERTX_APP}"
    sudo ln -s ${SOURCE_DIR}/ ${NETALERTX_APP}

    echo "      -> Mounting ramdisks for /log and /api"
    mkdir -p ${NETALERTX_LOG} ${NETALERTX_API}
    sudo mount -o uid=$(id -u netalertx),gid=$(id -g netalertx),mode=775 -t tmpfs -o size=256M tmpfs "${NETALERTX_LOG}"
    sudo mount -o uid=$(id -u netalertx),gid=$(id -g netalertx),mode=775 -t tmpfs -o size=256M tmpfs "${NETALERTX_API}"
    mkdir -p ${NETALERTX_PLUGINS_LOG}
    touch ${NETALERTX_PLUGINS_LOG}/.dockerignore ${NETALERTX_API}/.dockerignore
    # tmpfs mounts configured with netalertx ownership and 775 permissions above

    touch /app/log/nginx_error.log
    echo "      -> Empty log"|tee ${INSTALL_DIR}/log/app.log \
        ${INSTALL_DIR}/log/app_front.log \
        ${INSTALL_DIR}/log/stdout.log
    touch ${INSTALL_DIR}/log/stderr.log \
        ${INSTALL_DIR}/log/execution_queue.log
    echo 0 > ${INSTALL_DIR}/log/db_is_locked.log
    for f in ${INSTALL_DIR}/log/*.log; do
        sudo chown netalertx:www-data $f
        sudo chmod 664 $f
        echo "" > $f
    done

    mkdir -p /app/log/plugins
    sudo chown -R netalertx:www-data ${INSTALL_DIR}

    
    while ps ax | grep -v grep | grep python3 > /dev/null; do
        killall python3 &>/dev/null
        sleep 0.2
    done
	sudo chmod 777 /opt/venv/lib/python3.12/site-packages/ && \
    pip install --no-cache-dir debugpy docker && \
    sudo chmod 005 /opt/venv/lib/python3.12/site-packages/
	sudo chmod 666 /var/run/docker.sock

	echo "      -> Updating build timestamp"
	date +%s > ${NETALERTX_FRONT}/buildtimestamp.txt
    
}

# configure_php: configure PHP-FPM and enable dev debug options
configure_php() {
    echo "[3/4] Configuring PHP-FPM..."
    sudo chown -R netalertx:netalertx  ${SYSTEM_SERVICES_RUN} 2>/dev/null || true

}

# start_services: start crond, PHP-FPM, nginx and the application
start_services() {
    echo "[4/4] Starting services"

    sudo chmod +x /entrypoint.sh
    setsid bash /entrypoint.sh&
    sleep 1
}


sudo chmod 755 /app/
echo "Development $(git rev-parse --short=8 HEAD)"| sudo tee /app/.VERSION
# Run the main function
main

# create a services readme file
echo "This folder is auto-generated by the container and devcontainer setup.sh script." > /services/README.md
echo "Any changes here will be lost on rebuild. To make permanent changes, edit files in .devcontainer or production filesystem and rebuild the container." >> /services/README.md
echo "Only make temporary/test changes in this folder, then perform a rebuild to reset." >> /services/README.md




