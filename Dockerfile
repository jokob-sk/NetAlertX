FROM debian:buster-slim

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update \
    && apt-get install --no-install-recommends ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo lighttpd php php-cgi php-fpm php-sqlite3 sqlite3 dnsutils net-tools python iproute2 -y \
    && apt-get clean autoclean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /home/pi/pialert/install/index.html /var/www/html/index.html \
    && ln -s /home/pi/pialert/front /var/www/html/pialert \
    && lighttpd-enable-mod fastcgi-php
    # Redirect for lighthttpd to work properly

COPY . /home/pi/pialert

# Pi.Alert | also we probably should/can delete the tar from the repo and remove this line
RUN rm -r /home/pi/pialert/tar \
    && python /home/pi/pialert/back/pialert.py update_vendors \    
    && sed -ie 's/= 80/= 20211/g' /etc/lighttpd/lighttpd.conf \
    && (crontab -l 2>/dev/null; cat /home/pi/pialert/install/pialert.cron) | crontab -

EXPOSE 20211

# https://github.com/rtsp/docker-lighttpd/blob/main/Dockerfile
# > this one maybe better? https://hub.docker.com/r/jitesoft/lighttpd
# Todo, refacto CMD so that we can run lighttpd and make it respond instant
# The above Dockerfile is doing this well, but i don't see why it isn't working for us

CMD ["/home/pi/pialert/dockerfiles/start.sh"]
