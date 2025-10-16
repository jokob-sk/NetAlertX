#!/bin/sh
echo '
 _   _      _    ___  _           _  __   __
| \ | |    | |  / _ \| |         | | \ \ / /
|  \| | ___| |_/ /_\ \ | ___ _ __| |_ \ V / 
| .   |/ _ \ __|  _  | |/ _ \  __| __|/   \ 
| |\  |  __/ |_| | | | |  __/ |  | |_/ /^\ \
\_| \_/\___|\__\_| |_/_|\___|_|   \__\/   \/
   Network intruder and presence detector. 
   https://netalertx.com
'

set -u

bash /services/check-cap.sh
bash /services/check-ramdisk.sh
bash /services/check-first-run-config.sh
bash /services/check-first-run-db.sh
bash /services/check-app.sh



SERVICES=""
FAILED_NAME=""
FAILED_STATUS=0

is_pid_active() {
    pid="$1"
    [ -z "${pid}" ] && return 1

    if ! kill -0 "${pid}" 2>/dev/null; then
        return 1
    fi

    if [ -r "/proc/${pid}/status" ]; then
        state_line=$(grep '^State:' "/proc/${pid}/status" 2>/dev/null || true)
        case "${state_line}" in
            *"(zombie)"*|*"(dead)"*)
                return 1
                ;;
        esac
    fi

    return 0
}

add_service() {
    script="$1"
    name="$2"
    "$script" &
    pid=$!
    SERVICES="${SERVICES} ${pid}:${name}"
}

remove_service() {
    target_pid="$1"
    updated=""
    for entry in ${SERVICES}; do
        pid="${entry%%:*}"
        [ -z "${pid}" ] && continue
        [ "${pid}" = "${target_pid}" ] && continue
        updated="${updated} ${entry}"
    done
    SERVICES="${updated}"
}

shutdown_services() {
    for entry in ${SERVICES}; do
        pid="${entry%%:*}"
        [ -z "${pid}" ] && continue
        if is_pid_active "${pid}"; then
            kill "${pid}" 2>/dev/null || true
        fi
    done
    for entry in ${SERVICES}; do
        pid="${entry%%:*}"
        [ -z "${pid}" ] && continue
        wait "${pid}" 2>/dev/null || true
    done
    echo "All services stopped."
}

handle_exit() {
    if [ -n "${FAILED_NAME}" ]; then
        echo "Service ${FAILED_NAME} exited with status ${FAILED_STATUS}."
    fi
    shutdown_services
    exit "${FAILED_STATUS}"
}

on_signal() {
    echo "Caught signal, shutting down services..."
    FAILED_NAME="signal"
    FAILED_STATUS=143
    handle_exit
}

/services/update_vendors.sh &

trap on_signal INT TERM

[ ! -d "${NETALERTX_PLUGINS_LOG}" ] && mkdir -p "${NETALERTX_PLUGINS_LOG}"
[ ! -d "${SYSTEM_SERVICES_RUN_LOG}" ] && mkdir -p "${SYSTEM_SERVICES_RUN_LOG}"
[ ! -d "${SYSTEM_SERVICES_RUN_TMP}" ] && mkdir -p "${SYSTEM_SERVICES_RUN_TMP}"
[ ! -f "${LOG_DB_IS_LOCKED}" ] && touch "${LOG_DB_IS_LOCKED}"
[ ! -f "${LOG_EXECUTION_QUEUE}" ] && touch "${LOG_EXECUTION_QUEUE}"

if [ "${ENVIRONMENT:-}" ] && [ "${ENVIRONMENT:-}" != "debian" ]; then
    add_service "/services/start-crond.sh" "crond"
fi
add_service "/services/start-php-fpm.sh" "php-fpm83"
add_service "/services/start-nginx.sh" "nginx"
add_service "/services/start-backend.sh" "python3"


# if NETALERTX_DEBUG=1 then we will not kill any services if one fails. We will just wait for all to exit.
if [ "${NETALERTX_DEBUG:-0}" -eq 1 ]; then
	echo "NETALERTX_DEBUG is set to 1, will not shut down other services if one fails."
	wait
	exit $?
fi


# If any service fails, we will shut down all others and exit with the same status.
# This improves reliability in production environments by reinitializing the entire stack if one service fails.
while [ -n "${SERVICES}" ]; do
    for entry in ${SERVICES}; do
        pid="${entry%%:*}"
        name="${entry#*:}"
        [ -z "${pid}" ] && continue
        if ! is_pid_active "${pid}"; then
            wait "${pid}" 2>/dev/null
            status=$?
            FAILED_STATUS=$status
            FAILED_NAME="${name}"
            remove_service "${pid}"
            handle_exit
        fi

    done
    sleep 10
    ps -a
done

if [ "${FAILED_STATUS}" -eq 0 ] && [ "${FAILED_NAME}" != "signal" ]; then
    FAILED_STATUS=1
fi