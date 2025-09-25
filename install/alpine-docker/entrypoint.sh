#!/bin/bash

# Function to clean up background processes
cleanup() {
    echo "Caught signal, shutting down services..."
    # Kill all background jobs
    kill $(jobs -p)
    wait
    echo "All services stopped."
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM (docker stop)
trap cleanup SIGINT SIGTERM

# Start all necessary services for NetAlertX in the background
/services/start-crond.sh &
/services/start-php-fpm.sh &
/services/start-nginx.sh &
/services/start-backend.sh &

# Wait for any background process to exit
wait -n
# Trigger cleanup if any process exits
cleanup
