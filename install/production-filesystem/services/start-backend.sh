#!/bin/bash

cd "${NETALERTX_APP}" || exit 1
while $(ps ax | grep -v grep | grep python3 >/dev/null); do
	killall python3 &>/dev/null
	sleep 0.2
done

echo "python3 $(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null) -m server > >(tee /app/log/stdout.log) 2> >(tee /app/log/stderr.log >&2)"
exec python3 $(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null) -m server > >(tee /app/log/stdout.log) 2> >(tee /app/log/stderr.log >&2)
