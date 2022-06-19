#!/bin/sh

chmod -R o+w /home/pi/pialert/db
service cron start && lighttpd -D -f /etc/lighttpd/lighttpd.conf