#!/bin/bash
echo "Initializing nginx..."
# Setup NGINX
echo "Setting webserver to address ($LISTEN_ADDR) and port ($PORT)"
envsubst '$NETALERTX_FRONT $LISTEN_ADDR $PORT' < "${NETALERTX_APP}/dockerfiles/netalertx.template.conf" > "${NGINX_CONFIG_FILE}"
rm -f /etc/nginx/http.d/default.conf
# Set nginx permissions
chown nginx:nginx /run/nginx/ /var/log/nginx/ /var/lib/nginx/ /var/lib/nginx/tmp/
chgrp www-data /var/www/localhost/htdocs/
echo "nginx initialized."
