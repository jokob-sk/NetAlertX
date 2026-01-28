#! /bin/bash

set -euo pipefail

LOG_DIR=${NETALERTX_LOG}
RUN_DIR=${SYSTEM_SERVICES_RUN}
TMP_DIR=/tmp/nginx

# Create directories if they don't exist
mkdir -p "${LOG_DIR}" "${RUN_DIR}" "${TMP_DIR}"

nginx_pid=""

# Called externally, but shellcheck does not see that and claims it is unused.
# shellcheck disable=SC2329,SC2317
cleanup() {
	status=$?
	echo "nginx stopped! (exit ${status})"
}

# Called externally, but shellcheck does not see that and claims it is unused.
# shellcheck disable=SC2329,SC2317
forward_signal() {
	if [[ -n "${nginx_pid}" ]]; then
		kill -TERM "${nginx_pid}" 2>/dev/null || true
	fi
}


# When in devcontainer we must kill any existing nginx processes
while pgrep -x nginx >/dev/null 2>&1; do
	killall nginx &>/dev/null || true
	sleep 0.2
done

TEMP_CONFIG_FILE=$(mktemp "${TMP_DIR}/netalertx.conf.XXXXXX")

#In the event PUID is 0 we need to run nginx as root
#This is useful on legacy systems where we cannot provision root access to a binary
export NGINX_USER_DIRECTIVE=""
if [ "$(id -u)" -eq 0 ]; then
    NGINX_USER_DIRECTIVE="user root;"
fi

# ------------------------------------------------------------------
# BACKEND_PORT RESOLUTION
# ------------------------------------------------------------------
# Priority 1: APP_CONF_OVERRIDE (parsed via jq)
# Priority 2: GRAPHQL_PORT env var
# Priority 3: Default 20212

# Default
export BACKEND_PORT=20212

# Check env var
if [ -n "${GRAPHQL_PORT:-}" ]; then
    export BACKEND_PORT="${GRAPHQL_PORT}"
fi

# Check override (highest priority)
if [ -n "${APP_CONF_OVERRIDE:-}" ]; then
    override_port=$(echo "${APP_CONF_OVERRIDE}" | jq -r '.GRAPHQL_PORT // empty')
    if [ -n "${override_port}" ]; then
        export BACKEND_PORT="${override_port}"
    fi
fi

# Shell check doesn't recognize envsubst variables
# shellcheck disable=SC2016
if envsubst '${LISTEN_ADDR} ${PORT} ${NGINX_USER_DIRECTIVE} ${BACKEND_PORT}' < "${SYSTEM_NGINX_CONFIG_TEMPLATE}" > "${TEMP_CONFIG_FILE}" 2>/dev/null; then
	mv "${TEMP_CONFIG_FILE}" "${SYSTEM_SERVICES_ACTIVE_CONFIG_FILE}"
else
	echo "Note: Unable to write to ${SYSTEM_SERVICES_ACTIVE_CONFIG_FILE}. Using default configuration."
	rm -f "${TEMP_CONFIG_FILE}" 
fi

trap cleanup EXIT
trap forward_signal INT TERM

# Ensure temp dirs have correct permissions
chmod -R 777 "/tmp/nginx" 2>/dev/null || true



# Execute nginx with overrides
# echo the full nginx command then run it
echo "Starting /usr/sbin/nginx -p \"${RUN_DIR}/\" -c \"${SYSTEM_SERVICES_ACTIVE_CONFIG_FILE}\" -g \"error_log stderr; error_log ${NETALERTX_LOG}/nginx-error.log; daemon off;\" &"
/usr/sbin/nginx \
	-p "${RUN_DIR}/" \
	-c "${SYSTEM_SERVICES_ACTIVE_CONFIG_FILE}" \
	-g "error_log stderr; error_log ${NETALERTX_LOG}/nginx-error.log; daemon off;" &
nginx_pid=$!

wait "${nginx_pid}"
nginx_exit=$?
echo -ne " done"
exit ${nginx_exit}
