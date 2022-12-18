FROM debian:bullseye-slim

# default UID and GID
ENV USER=pi USER_ID=1000 USER_GID=1000 TZ=Europe/London PORT=20211

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

# create pi user and group
# add root and www-data to pi group so they can r/w files and db
RUN groupadd --gid "${USER_GID}" "${USER}" && \
    useradd \
        --uid ${USER_ID} \
        --gid ${USER_GID} \
        --create-home \
        --shell /bin/bash \
        ${USER} && \
    usermod -a -G ${USER_GID} root && \
    usermod -a -G ${USER_GID} www-data

COPY --chmod=775 --chown=${USER_ID}:${USER_GID} . /home/pi/pialert/

# Pi.Alert
RUN rm /etc/nginx/sites-available/default \
    && ln -s /home/pi/pialert/install/default /etc/nginx/sites-available/default \
    && sed -ie 's/listen 80/listen '${PORT}'/g' /etc/nginx/sites-available/default \
    # run the hardware vendors update
    && /home/pi/pialert/back/update_vendors.sh 

ENTRYPOINT ["tini", "--"]

CMD ["/home/pi/pialert/dockerfiles/start.sh"]
