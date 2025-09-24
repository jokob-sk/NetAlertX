#!/bin/bash
echo "Starting crond..."
exec /usr/sbin/crond -f -L /dev/stdout
