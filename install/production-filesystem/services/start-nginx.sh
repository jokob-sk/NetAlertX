#! /bin/bash

set -euo pipefail

LOG_DIR=${NETALERTX_LOG}
RUN_DIR=${SYSTEM_SERVICES_RUN}
TMP_DIR=${SYSTEM_SERVICES_RUN_TMP}
SYSTEM_NGINX_CONFIG_TEMPLATE="/services/config/nginx/netalertx.conf.template"
SYSTEM_NGINX_CONFIG_FILE="/services/config/nginx/conf.active/netalertx.conf"

# Create directories if they don't exist
mkdir -p "${LOG_DIR}" "${RUN_DIR}" "${TMP_DIR}"

echo "Starting nginx..."

nginx_pid=""

cleanup() {
	status=$?
	echo "nginx stopped! (exit ${status})"
}

forward_signal() {
	if [[ -n "${nginx_pid}" ]]; then
		kill -TERM "${nginx_pid}" 2>/dev/null || true
	fi
}


# When in devcontainer we must kill any existing nginx processes
while ps ax | grep -v -e "grep" -e "nginx.sh" | grep nginx >/dev/null 2>&1; do
	killall nginx &>/dev/null || true
	sleep 0.2
done

TEMP_CONFIG_FILE=$(mktemp "${TMP_DIR}/netalertx.conf.XXXXXX")
if envsubst '${LISTEN_ADDR} ${PORT}' < "${SYSTEM_NGINX_CONFIG_TEMPLATE}" > "${TEMP_CONFIG_FILE}" 2>/dev/null; then
	mv "${TEMP_CONFIG_FILE}" "${SYSTEM_NGINX_CONFIG_FILE}" 
else
	echo "Note: Unable to write to ${SYSTEM_NGINX_CONFIG_FILE}. Using default configuration."
	rm -f "${TEMP_CONFIG_FILE}" 
fi

trap cleanup EXIT
trap forward_signal INT TERM



# Execute nginx with overrides
# echo the full nginx command then run it
echo "nginx command:"
echo "	nginx \
	-p \"${RUN_DIR}/\" \
	-c \"${SYSTEM_NGINX_CONFIG_FILE}\" \
	-g \"error_log ${NETALERTX_LOG}/nginx-error.log; pid ${RUN_DIR}/nginx.pid; daemon off;\" &"
nginx \
	-p "${RUN_DIR}/" \
	-c "${SYSTEM_NGINX_CONFIG_FILE}" \
	-g "error_log ${NETALERTX_LOG}/nginx-error.log; pid ${RUN_DIR}/nginx.pid; daemon off;" &
nginx_pid=$!

wait "${nginx_pid}"
echo -ne " done"
exit $?
