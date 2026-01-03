#!/bin/sh

LOGFILE="/workspaces/NetAlertX/test-script.log"
CMD="/usr/bin/python -m pytest -q test/docker_tests/test_container_environment.py -k missing_app_conf_triggers_seed --maxfail=1 -vv"

echo "Running: ${CMD}" | tee "${LOGFILE}"
${CMD} 2>&1 | tee -a "${LOGFILE}"
