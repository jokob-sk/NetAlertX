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

while ps ax | grep -v -e grep -e '.sh' | grep crond >/dev/null 2>&1; do
	killall crond &>/dev/null
	sleep 0.2
done

trap cleanup EXIT
trap forward_signal INT TERM

echo "/usr/sbin/crond -c \"${SYSTEM_SERVICES_CROND}\" -f -L \"${LOG_CROND}\" >>\"${LOG_CROND}\" 2>&1 &"

/usr/sbin/crond -c "${SYSTEM_SERVICES_CROND}" -f -L "${LOG_CROND}" >>"${LOG_CROND}" 2>&1 &
crond_pid=$!

wait "${crond_pid}"; status=$?
echo -ne " done"
exit ${status}
