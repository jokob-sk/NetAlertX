#!/bin/sh
/etc/init.d/php7.4-fpm start
/etc/init.d/nginx start
python /home/pi/pialert/back/pialert.py
