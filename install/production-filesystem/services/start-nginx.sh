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

# Shell check doesn't recognize envsubst variables
# shellcheck disable=SC2016
if envsubst '${LISTEN_ADDR} ${PORT}' < "${SYSTEM_NGINX_CONFIG_TEMPLATE}" > "${TEMP_CONFIG_FILE}" 2>/dev/null; then
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
echo "Starting /usr/sbin/nginx -p \"${RUN_DIR}/\" -c \"${SYSTEM_SERVICES_ACTIVE_CONFIG_FILE}\" -g \"error_log /dev/stderr; error_log ${NETALERTX_LOG}/nginx-error.log; daemon off;\" &"
/usr/sbin/nginx \
	-p "${RUN_DIR}/" \
	-c "${SYSTEM_SERVICES_ACTIVE_CONFIG_FILE}" \
	-g "error_log /dev/stderr; error_log ${NETALERTX_LOG}/nginx-error.log; daemon off;" &
nginx_pid=$!

wait "${nginx_pid}"
nginx_exit=$?
echo -ne " done"
exit ${nginx_exit}
