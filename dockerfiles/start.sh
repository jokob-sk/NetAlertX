#!/bin/sh
/home/pi/pialert/dockerfiles/user-mapping.sh

# if custom variables not set we do not need to do anything
if [ -n "${TZ}" ]; then    
  FILECONF=/home/pi/pialert/config/pialert.conf 
  if [ -f "$FILECONF" ]; then
    sed -ie "s|Europe/Berlin|${TZ}|g" /home/pi/pialert/config/pialert.conf 
  else 
    sed -ie "s|Europe/Berlin|${TZ}|g" /home/pi/pialert/back/pialert.conf_bak 
  fi
fi

if [ -n "${PORT}" ]; then  
  sed -ie 's/listen 20211/listen '${PORT}'/g' /etc/nginx/sites-available/default
fi 

# I hope this will fix DB permission issues going forward
FILEDB=/home/pi/pialert/db/pialert.db
if [ -f "$FILEDB" ]; then
    chown -R www-data:www-data /home/pi/pialert/db/pialert.db
fi

chmod -R a+rw /home/pi/pialert/front/log
chmod -R a+rw /home/pi/pialert/config

/etc/init.d/php7.4-fpm start
/etc/init.d/nginx start

# cron -f
#python /home/pi/pialert/back/pialert.py
echo "DATA MONKEY VERSION ..."
python /home/pi/pialert/pialert/pialert.py
