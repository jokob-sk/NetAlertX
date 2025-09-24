#!/bin/bash
echo "Starting php-fpm..."
exec /usr/sbin/php-fpm83 -F >> "${LOG_APP_PHP_ERRORS}" 2>&1
