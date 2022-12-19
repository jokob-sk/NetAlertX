FROM debian:bullseye-slim

ENV TZ=Europe/London

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update \
    && apt-get install --no-install-recommends tini ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo nginx-light php php-cgi php-fpm php-sqlite3 php-curl sqlite3 dnsutils net-tools python3 iproute2 nmap python3-pip zip -y \
    && pip3 install requests paho-mqtt  \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 \
    && apt-get clean autoclean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/www/html \
    && ln -s /home/pi/pialert/front /var/www/html 
 
   
# now creating user
RUN useradd \
    --create-home \
    --shell /bin/bash \
    pi

COPY . /home/pi/pialert

# Pi.Alert 
RUN rm /etc/nginx/sites-available/default \
  	&& ln -s /home/pi/pialert/install/default /etc/nginx/sites-available/default \
    # run the hardware vendors update
    && /home/pi/pialert/back/update_vendors.sh 

# it's easy for permissions set in Git to be overridden, so doing it manually
RUN chown -R pi:www-data /home/pi/pialert/

CMD ["/home/pi/pialert/docker-entrypoint.sh"]