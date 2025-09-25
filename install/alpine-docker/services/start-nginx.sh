#!/bin/bash
echo "Starting nginx..."
exec nginx \
    -c "${NGINX_CONFIG_FILE}" \
    -g "daemon off;" >> "${LOG_APP_FRONT}" 2>&1
