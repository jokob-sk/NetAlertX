#!/bin/bash
echo "Starting nginx..."
exec nginx -g "daemon off;" >> "${LOG_APP_FRONT}" 2>&1
