#!/bin/bash
echo "Initializing crond..."
# Add crontab file
cp -f ${NETALERTX_APP}/install/crontab /etc/crontabs/root
chmod 600 /etc/crontabs/root
chown root:root /etc/crontabs/root
echo "crond initialized."
