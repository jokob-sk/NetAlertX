#!/bin/sh

/etc/init.d/lighttpd start
service cron start && tail -f /dev/null
