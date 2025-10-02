#!/bin/bash

cd "${NETALERTX_APP}" || exit 1

exec python3 $(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null) -m server > >(tee /app/log/stdout.log) 2> >(tee /app/log/stderr.log >&2)
