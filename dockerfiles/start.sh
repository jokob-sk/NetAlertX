#!/bin/sh
/home/pi/pialert/dockerfiles/user-mapping.sh


#chmod -R 755 /var/www/html/pialert
#chmod -R o+w /home/pi/pialert/db
/etc/init.d/lighttpd start
cron -f
