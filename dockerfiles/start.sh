#!/bin/sh

chmod -R +w /home/pi/pialert/db
/etc/init.d/lighttpd start
service cron start && tail -f /dev/null
