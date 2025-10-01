#!/bin/bash
set -euo pipefail

echo "Starting crond..."

crond_pid=""

cleanup() {
	status=$?
	echo "Crond stopped! (exit ${status})"
}

forward_signal() {
	if [[ -n "${crond_pid}" ]]; then
		kill -TERM "${crond_pid}" 2>/dev/null || true
	fi
}

trap cleanup EXIT
trap forward_signal INT TERM

/usr/sbin/crond -c "${SYSTEM_SERVICES_CROND}" -f -L "${LOG_CROND}" >> "${LOG_CROND}" 2>&1 &
crond_pid=$!

wait "${crond_pid}"
exit $?