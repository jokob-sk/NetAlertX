#!/bin/sh

chmod -R o+w /home/pi/pialert/db
# /etc/init.d/lighttpd start
service cron start && nohup (/usr/sbin/lighttpd -D -f /etc/lighttpd/lighttpd.conf) &