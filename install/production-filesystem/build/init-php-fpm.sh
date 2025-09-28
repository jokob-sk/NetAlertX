#!/bin/bash
echo "Initializing php-fpm..."
# Set up PHP-FPM directories and socket configuration
install -d -o netalertx -g netalertx /run/php/


echo "php-fpm initialized."
