#!/bin/sh
/home/pi/pialert/dockerfiles/user-mapping.sh
# probably too broad permissions
chmod -R 755 /home/pi/pialert  
chmod -R 755 /var/www/html/pialert
chmod -R o+w /home/pi/pialert/db
/etc/init.d/lighttpd start
service cron start && tail -f /dev/null