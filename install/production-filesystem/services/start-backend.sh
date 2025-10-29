#!/bin/bash

cd "${NETALERTX_APP}" || exit 1
max_attempts=50  # 10 seconds total (50 * 0.2s)
attempt=0
while ps ax | grep -v grep | grep -q python3 && [ $attempt -lt $max_attempts ]; do
	killall -TERM python3 &>/dev/null
	sleep 0.2
	((attempt++))
done
# Force kill if graceful shutdown failed
killall -KILL python3 &>/dev/null

echo "Starting python3 $(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null) -m server > /app/log/stdout.log 2> >(tee /app/log/stderr.log >&2)"
exec python3 $(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null) -m server > /app/log/stdout.log 2> >(tee /app/log/stderr.log >&2)
