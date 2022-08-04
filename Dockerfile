FROM debian:bullseye-slim

# default UID and GID
ENV USER=pi USER_ID=1000 USER_GID=1000 TZ=Europe/London PORT=20211

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update \
    && apt-get install --no-install-recommends ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo lighttpd php php-cgi php-fpm php-sqlite3 sqlite3 dnsutils net-tools python3 iproute2 nmap python3-pip zip -y \
    && pip3 install requests  \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 \
    && apt-get clean autoclean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/www/html \
    && ln -s /home/pi/pialert/front /var/www/html \
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
RUN python /home/pi/pialert/back/pialert.py update_vendors \    
    && sed -ie 's/= 80/= '${PORT}'/g' /etc/lighttpd/lighttpd.conf \
    && (crontab -l 2>/dev/null; cat /home/pi/pialert/install/pialert.cron) | crontab -

# it's easy for permissions set in Git to be overridden, so doing it manually
RUN chmod -R a+rxw /home/pi/pialert/

CMD ["/home/pi/pialert/dockerfiles/start.sh"]
