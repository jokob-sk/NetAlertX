#!/bin/bash
echo "Initializing nginx..."
# Setup NGINX
echo "Setting webserver to address ($LISTEN_ADDR) and port ($PORT)"
envsubst '$NETALERTX_APP $LISTEN_ADDR $PORT' < "${NETALERTX_APP}/install/netalertx.template.conf" > "${NGINX_CONFIG_FILE}"
rm -f /etc/nginx/http.d/default.conf
echo "nginx initialized."
