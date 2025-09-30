#!/bin/bash
echo "Initializing php-fpm..."
# Set up PHP-FPM directories and socket configuration
install -d -o netalertx -g netalertx /services/config/run


echo "php-fpm initialized."
