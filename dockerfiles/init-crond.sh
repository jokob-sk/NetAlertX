#!/bin/bash
echo "Initializing crond..."
# Add crontab file

chmod 600 /etc/crontabs/root
chown root:root /etc/crontabs/root
echo "crond initialized."
