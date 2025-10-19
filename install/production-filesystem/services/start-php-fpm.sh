#!/bin/bash
set -euo pipefail

echo "Starting php-fpm..."

php_fpm_pid=""

cleanup() {
	status=$?
	echo "php-fpm stopped! (exit ${status})"
}

forward_signal() {
	if [[ -n "${php_fpm_pid}" ]]; then
		kill -TERM "${php_fpm_pid}" 2>/dev/null || true
	fi
}

while ps ax | grep -v grep | grep php-fpm83 >/dev/null; do
	killall php-fpm83 &>/dev/null
	sleep 0.2
done

trap cleanup EXIT
trap forward_signal INT TERM

echo "/usr/sbin/php-fpm83 -y \"${PHP_FPM_CONFIG_FILE}\" -F >>\"${LOG_APP_PHP_ERRORS}\" 2>&1 &"
/usr/sbin/php-fpm83 -y "${PHP_FPM_CONFIG_FILE}" -F >>"${LOG_APP_PHP_ERRORS}" 2>&1 &
php_fpm_pid=$!

wait "${php_fpm_pid}"
echo -ne " done"
exit $?
