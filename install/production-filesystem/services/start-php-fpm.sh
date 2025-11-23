#!/bin/bash
set -euo pipefail

php_fpm_pid=""

# Called externally, but shellcheck does not see that and claims it is unused.
# shellcheck disable=SC2329,SC2317
cleanup() {
	status=$?
	echo "php-fpm stopped! (exit ${status})"
}

# Called externally, but shellcheck does not see that and claims it is unused.
# shellcheck disable=SC2329,SC2317
forward_signal() {
	if [[ -n "${php_fpm_pid}" ]]; then
		kill -TERM "${php_fpm_pid}" 2>/dev/null || true
	fi
}

while pgrep -x php-fpm83 >/dev/null; do
	killall php-fpm83 &>/dev/null
	sleep 0.2
done

trap cleanup EXIT
trap forward_signal INT TERM

echo "Starting /usr/sbin/php-fpm83 -y \"${PHP_FPM_CONFIG_FILE}\" -F >>\"${LOG_APP_PHP_ERRORS}\" 2>/dev/stderr &"
/usr/sbin/php-fpm83 -y "${PHP_FPM_CONFIG_FILE}" -F >>"${LOG_APP_PHP_ERRORS}" 2> /dev/stderr &
php_fpm_pid=$!

wait "${php_fpm_pid}"
exit_status=$?
echo -ne " done"
exit $exit_status