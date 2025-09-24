#!/bin/bash

# Start all necessary services for NetAlertX
/services/start-crond.sh &
/services/start-php-fpm.sh &
/services/start-nginx.sh &
/services/start-backend.sh 
