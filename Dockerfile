FROM debian:buster-slim

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update \
    && apt-get install --no-install-recommends ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo lighttpd php php-cgi php-fpm php-sqlite3 sqlite3 dnsutils net-tools python iproute2 -y \
    && apt-get clean autoclean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

# Lighttpd & PHP
RUN mv /var/www/html/index.lighttpd.html /var/www/html/index.lighttpd.html.old \
    && ln -s /home/pi/pialert/install/index.html /var/www/html/index.html \
    && lighttpd-enable-mod fastcgi-php 

COPY . /home/pi/pialert

# Todo, is this tar part still needed?

# delete .git/ files and the tar/ realese directory to make the image smaller
#RUN rm -r /home/pi/pialert/.git \
RUN rm -r /home/pi/pialert/tar 

# Todo, do we need to restart lighthttpd?

# Pi.Alert   
RUN ln -s /home/pi/pialert/front /var/www/html/pialert  \
    && python /home/pi/pialert/back/pialert.py update_vendors \    
    && (crontab -l 2>/dev/null; cat /home/pi/pialert/install/pialert.cron) | crontab - \
    && chgrp -R www-data /home/pi/pialert/db \
    && chmod -R 770 /home/pi/pialert/db \
    # changing the default port number 80 to something random, here 20211
    && sed -ie 's/= 80/= 20211/g' /etc/lighttpd/lighttpd.conf \
    && service lighttpd restart 

EXPOSE 20211

# Todo, can we just use CMD and ENTRYPOINT instead of a script?

CMD ["/home/pi/pialert/dockerfiles/start.sh"]