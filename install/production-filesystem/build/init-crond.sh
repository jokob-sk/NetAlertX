#!/bin/bash
echo "Initializing crond..."
# Add crontab file
rm /etc/crontabs/root
chmod 600 /etc/crontabs/netalertx
chown netalertx:netalertx /etc/crontabs/netalertx
echo "crond initialized."
