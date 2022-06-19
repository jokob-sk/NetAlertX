#!/bin/sh

chmod -R o+w /home/pi/pialert/db
/etc/init.d/lighttpd start
cron && tail -f /var/log/cron.log