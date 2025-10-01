#!/bin/bash
echo "Initializing nginx..."
install -d -o netalertx -g netalertx -m 700 /app/run/tmp/client_body;
echo "nginx initialized."