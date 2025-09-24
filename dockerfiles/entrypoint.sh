#!/bin/bash

echo "---------------------------------------------------------"
echo "[ENTRYPOINT] Initializing container..."
echo "---------------------------------------------------------"

# Run the main initialization script
/app/dockerfiles/init.sh

echo "---------------------------------------------------------"
echo "[ENTRYPOINT] Starting services..."
echo "---------------------------------------------------------"

# Start all services in the background
/app/dockerfiles/start-crond.sh &
/app/dockerfiles/start-php-fpm.sh &
/app/dockerfiles/start-nginx.sh &
/app/dockerfiles/start-backend.sh &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
