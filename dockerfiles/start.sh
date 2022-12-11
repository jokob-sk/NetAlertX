#!/bin/sh
/home/pi/pialert/dockerfiles/user-mapping.sh

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then    
  sed -ie "s|Europe/Berlin|${TZ}|g" /home/pi/pialert/config/pialert.conf    
fi

if [ -n "${PORT}" ]; then  
  sed -ie 's/listen 20211/listen '${PORT}'/g' /etc/nginx/sites-available/default
fi

# I hope this will fix DB permission issues going forward
chown -R www-data:www-data /home/pi/pialert/db/pialert.db

chmod -R a+rw /home/pi/pialert/front/log

/etc/init.d/php7.4-fpm start
/etc/init.d/nginx start

# cron -f

python /home/pi/pialert/back/pialert.py  > /home/pi/pialert/front/log/pialert.log    2>&1
