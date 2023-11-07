FROM debian:bookworm-slim

# default UID and GID
ENV USER=pi USER_ID=1000 USER_GID=1000  PORT=20211 
#TZ=Europe/London

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update 
RUN apt-get install sudo -y 


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


# ❗ IMPORTANT - if you modify this file modify the /install/install_dependecies.sh file as well ❗ 

RUN apt-get install -y \
    tini snmp ca-certificates curl libwww-perl arp-scan perl apt-utils cron sudo \
    nginx-light php php-cgi php-fpm php-sqlite3 php-curl sqlite3 dnsutils net-tools \
    python3 iproute2 nmap python3-pip zip systemctl usbutils traceroute

# Alternate dependencies
RUN apt-get install nginx nginx-core mtr php-fpm php8.2-fpm php-cli php8.2 php8.2-sqlite3 -y
RUN phpenmod -v 8.2 sqlite3 

# Setup virtual python environment and use pip3 to install packages
RUN apt-get install -y python3-venv
RUN python3 -m venv myenv
RUN /bin/bash -c "source myenv/bin/activate && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 && pip3 install requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet"


CMD ["/home/pi/pialert/dockerfiles/start.sh"]


