#!/bin/bash
echo "Initializing nginx..."
install -d -o netalertx -g netalertx -m 700 ${SYSTEM_SERVICES_RUN_TMP}/client_body;
echo "nginx initialized."