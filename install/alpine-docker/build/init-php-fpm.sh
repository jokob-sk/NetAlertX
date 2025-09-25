#!/bin/bash
echo "Initializing php-fpm..."
# Set up PHP-FPM directories and socket configuration
install -d -o nginx -g www-data /run/php/
sed -i "/^;pid/c\pid = /run/php/php8.3-fpm.pid" /etc/php83/php-fpm.conf
sed -i "/^listen/c\listen = /run/php/php8.3-fpm.sock" /etc/php83/php-fpm.d/www.conf
sed -i "/^;listen.owner/c\listen.owner = nginx" /etc/php83/php-fpm.d/www.conf
sed -i "/^;listen.group/c\listen.group = www-data" /etc/php83/php-fpm.d/www.conf
sed -i "/^user/c\user = nginx" /etc/php83/php-fpm.d/www.conf
sed -i "/^group/c\group = www-data" /etc/php83/php-fpm.d/www.conf

# Increase max child process count
sed -i -e 's/pm.max_children = 5/pm.max_children = 10/' /etc/php83/php-fpm.d/www.conf 

# Set error log path
sed -i "/^;*error_log\s*=/c\error_log = ${LOG_APP_PHP_ERRORS}" /etc/php83/php-fpm.conf
# If the line was not found, append it to the end of the file
if ! grep -q '^error_log\s*=' /etc/php83/php-fpm.conf; then
    echo "error_log = ${LOG_APP_PHP_ERRORS}" >> /etc/php83/php-fpm.conf
fi

echo "php-fpm initialized."
