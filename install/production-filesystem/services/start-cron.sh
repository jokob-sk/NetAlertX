#!/bin/bash
set -euo pipefail


crond_pid=""

# Called externally, but shellcheck does not see that and claims it is unused.
# shellcheck disable=SC2329,SC2317
cleanup() {
	status=$?
	echo "Supercronic stopped! (exit ${status})"
}

# Called externally, but shellcheck does not see that and claims it is unused.
# shellcheck disable=SC2329,SC2317
forward_signal() {
	if [[ -n "${crond_pid}" ]]; then
		kill -TERM "${crond_pid}" 2>/dev/null || true
	fi
}

while pgrep -x crond >/dev/null 2>&1; do
	killall crond &>/dev/null
	sleep 0.2
done

trap cleanup EXIT
trap forward_signal INT TERM

CRON_OPTS="--quiet"
if [ "${NETALERTX_DEBUG:-0}" -eq 1 ]; then
  CRON_OPTS="--debug"
fi

echo "Starting supercronic ${CRON_OPTS} \"${SYSTEM_SERVICES_CONFIG_CRON}/crontab\" >>\"${LOG_CRON}\" 2>&1 &"

supercronic ${CRON_OPTS} "${SYSTEM_SERVICES_CONFIG_CRON}/crontab" >>"${LOG_CRON}" 2>&1 &
crond_pid=$!

wait "${crond_pid}"; status=$?
echo -ne " done"
exit ${status}