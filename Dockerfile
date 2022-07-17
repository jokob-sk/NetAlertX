FROM debian:buster-slim

# default UID and GID
ENV USER=pi USER_ID=1000 USER_GID=1000 TZ=Europe/London PORT=20211

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update \
    && apt-get install --no-install-recommends ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo lighttpd php php-cgi php-fpm php-sqlite3 sqlite3 dnsutils net-tools python iproute2 nmap -y \
    && apt-get clean autoclean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /home/pi/pialert/install/index.html /var/www/html/index.html \
    && ln -s /home/pi/pialert/front /var/www/html/pialert \
    && lighttpd-enable-mod fastcgi-php 
 
   
# now creating user
RUN groupadd --gid "${USER_GID}" "${USER}" && \
    useradd \
      --uid ${USER_ID} \
      --gid ${USER_GID} \
      --create-home \
      --shell /bin/bash \
      ${USER}

COPY . /home/pi/pialert

# Pi.Alert 
RUN sed -ie "s|TIMEZONE|${TZ}|g" /home/pi/pialert/install/pialert.cron \
    && python /home/pi/pialert/back/pialert.py update_vendors \    
    && sed -ie 's/= 80/= '${PORT}'/g' /etc/lighttpd/lighttpd.conf \
    && (crontab -l 2>/dev/null; cat /home/pi/pialert/install/pialert.cron) | crontab -

# it's easy for permissions set in Git to be overridden, so doing it manually
RUN chmod -R a+rxw /home/pi/pialert/

CMD ["/home/pi/pialert/dockerfiles/start.sh"]
