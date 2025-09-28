#!/bin/bash
echo "Starting php-fpm..."
exec /usr/sbin/php-fpm83 -y ${PHP_FPM_CONFIG_FILE} -F >> "${LOG_APP_PHP_ERRORS}" 2>&1
