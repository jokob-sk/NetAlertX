#!/bin/bash
echo "Starting crond..."
exec /usr/sbin/crond -c ${SYSTEM_SERVICES_CROND} -f -L "${LOG_CROND}"
