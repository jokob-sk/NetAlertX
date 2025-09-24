FROM alpine:3.22 AS builder

ARG INSTALL_DIR=/app

ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apk add --no-cache bash shadow python3 python3-dev gcc musl-dev libffi-dev openssl-dev git \
    && python -m venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir -p ${INSTALL_DIR}
COPY api ${INSTALL_DIR}/api
COPY back ${INSTALL_DIR}/back
COPY config ${INSTALL_DIR}/config
COPY db ${INSTALL_DIR}/db
COPY dockerfiles ${INSTALL_DIR}/dockerfiles
COPY front ${INSTALL_DIR}/front
COPY server ${INSTALL_DIR}/server

#COPY . ${INSTALL_DIR}/

RUN pip install openwrt-luci-rpc asusrouter asyncio aiohttp graphene flask flask-cors unifi-sm-api tplink-omada-client wakeonlan pycryptodome requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet python-nmap dnspython librouteros yattag git+https://github.com/foreign-sub/aiofreepybox.git

RUN bash -c "find ${INSTALL_DIR} -type d -exec chmod 750 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f -exec chmod 640 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f \( -name '*.sh' -o -name '*.py'  -o -name 'speedtest-cli' \) -exec chmod 750 {} \;"

# Append Iliadbox certificate to aiofreepybox
COPY install/freebox_certificate.pem /opt/venv/lib/python3.12/site-packages/aiofreepybox/freebox_certificates.pem

# second stage
FROM alpine:3.22 AS runner

ARG INSTALL_DIR=/app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/sbin/usermod /usr/sbin/groupmod /usr/sbin/

# Enable venv
ENV PATH="/opt/venv/bin:$PATH" 

# default port and listen address
ENV PORT=20211 LISTEN_ADDR=0.0.0.0 GRAPHQL_PORT=20212

# needed for s6-overlay
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

# NetAlertX app directories
ENV NETALERTX_APP=/app
ENV NETALERTX_CONFIG=${NETALERTX_APP}/config
ENV NETALERTX_FRONT=${NETALERTX_APP}/front
ENV NETALERTX_SERVER=${NETALERTX_APP}/server
ENV NETALERTX_API=${NETALERTX_APP}/api
ENV NETALERTX_DB=${NETALERTX_APP}/db
ENV NETALERTX_BACK=${NETALERTX_APP}/back
ENV NETALERTX_LOG=${NETALERTX_APP}/log
ENV NETALERTX_PLUGINS_LOG=${NETALERTX_LOG}/plugins

# NetAlertX log files
ENV LOG_IP_CHANGES=${NETALERTX_LOG}/IP_changes.log
ENV LOG_APP=${NETALERTX_LOG}/app.log
ENV LOG_APP_FRONT=${NETALERTX_LOG}/app_front.log
ENV LOG_REPORT_OUTPUT_TXT=${NETALERTX_LOG}/report_output.txt
ENV LOG_DB_IS_LOCKED=${NETALERTX_LOG}/db_is_locked.log
ENV LOG_REPORT_OUTPUT_HTML=${NETALERTX_LOG}/report_output.html
ENV LOG_STDERR=${NETALERTX_LOG}/stderr.log
ENV LOG_APP_PHP_ERRORS=${NETALERTX_LOG}/app.php_errors.log
ENV LOG_EXECUTION_QUEUE=${NETALERTX_LOG}/execution_queue.log
ENV LOG_REPORT_OUTPUT_JSON=${NETALERTX_LOG}/report_output.json
ENV LOG_STDOUT=${NETALERTX_LOG}/stdout.log

# Important configuration files
ENV NGINX_CONFIG_FILE="/etc/nginx/http.d/netalertx.conf"
ENV NETALERTX_CONFIG_FILE=${NETALERTX_CONFIG}/app.conf
ENV NETALERTX_DB_FILE=${NETALERTX_DB}/app.db

# ❗ IMPORTANT - if you modify this file modify the /install/install_dependecies.sh file as well ❗ 

RUN apk update --no-cache \
    && apk add --no-cache bash libbsd zip lsblk gettext-envsubst sudo mtr tzdata s6-overlay \
    && apk add --no-cache curl arp-scan iproute2 iproute2-ss nmap nmap-scripts traceroute nbtscan avahi avahi-tools openrc dbus net-tools net-snmp-tools bind-tools awake ca-certificates \
    && apk add --no-cache sqlite php83 php83-fpm php83-cgi php83-curl php83-sqlite3 php83-session \
    && apk add --no-cache python3 nginx \
    && ln -s /usr/bin/awake /usr/bin/wakeonlan \
    && bash -c "install -d -m 750 -o nginx -g www-data ${INSTALL_DIR} ${INSTALL_DIR}" \
    && rm -f /etc/nginx/http.d/default.conf

COPY --from=builder --chown=nginx:www-data ${INSTALL_DIR}/ ${INSTALL_DIR}/

# Create required directories
RUN mkdir -p ${INSTALL_DIR}/config ${INSTALL_DIR}/db ${INSTALL_DIR}/log/plugins

# Add crontab file
COPY --chmod=600 --chown=root:root install/crontab /etc/crontabs/root

# Add healthcheck script
COPY --chmod=755 dockerfiles/healthcheck.sh /usr/local/bin/healthcheck.sh

# Create empty log files and API files
RUN touch ${INSTALL_DIR}/log/app.log \
    && touch ${INSTALL_DIR}/log/execution_queue.log \
    && touch ${INSTALL_DIR}/log/app_front.log \
    && touch ${INSTALL_DIR}/log/app.php_errors.log \
    && touch ${INSTALL_DIR}/log/stderr.log \
    && touch ${INSTALL_DIR}/log/stdout.log \
    && touch ${INSTALL_DIR}/log/db_is_locked.log \
    && touch ${INSTALL_DIR}/log/IP_changes.log \
    && touch ${INSTALL_DIR}/log/report_output.txt \
    && touch ${INSTALL_DIR}/log/report_output.html \
    && touch ${INSTALL_DIR}/log/report_output.json \
    && touch ${INSTALL_DIR}/api/user_notifications.json



# Set up PHP-FPM directories and socket configuration
RUN install -d -o nginx -g www-data /run/php/ \
    && sed -i "/^;pid/c\pid = /run/php/php8.3-fpm.pid" /etc/php83/php-fpm.conf \
    && sed -i "/^listen/c\listen = /run/php/php8.3-fpm.sock" /etc/php83/php-fpm.d/www.conf \
    && sed -i "/^;listen.owner/c\listen.owner = nginx" /etc/php83/php-fpm.d/www.conf \
    && sed -i "/^;listen.group/c\listen.group = www-data" /etc/php83/php-fpm.d/www.conf \
    && sed -i "/^user/c\user = nginx" /etc/php83/php-fpm.d/www.conf \
    && sed -i "/^group/c\group = www-data" /etc/php83/php-fpm.d/www.conf

# Set up s6 overlay service directories
RUN mkdir -p /etc/s6-overlay/s6-rc.d/SetupOneshot \
    && mkdir -p /etc/s6-overlay/s6-rc.d/crond/dependencies.d \
    && mkdir -p /etc/s6-overlay/s6-rc.d/php-fpm/dependencies.d \
    && mkdir -p /etc/s6-overlay/s6-rc.d/nginx/dependencies.d \
    && mkdir -p /etc/s6-overlay/s6-rc.d/netalertx/dependencies.d

# Set up s6 overlay service types and scripts
RUN echo "oneshot" > /etc/s6-overlay/s6-rc.d/SetupOneshot/type \
    && echo "longrun" > /etc/s6-overlay/s6-rc.d/crond/type \
    && echo "longrun" > /etc/s6-overlay/s6-rc.d/php-fpm/type \
    && echo "longrun" > /etc/s6-overlay/s6-rc.d/nginx/type \
    && echo "longrun" > /etc/s6-overlay/s6-rc.d/netalertx/type

# Create s6 overlay service scripts
RUN echo -e "${INSTALL_DIR}/dockerfiles/init.sh" > /etc/s6-overlay/s6-rc.d/SetupOneshot/up \
    && echo -e '#!/bin/execlineb -P\n\nif { echo\n"\n[INSTALL] Starting crond service...\n\n" }\n/usr/sbin/crond -f' > /etc/s6-overlay/s6-rc.d/crond/run \
    && echo -e "#!/bin/execlineb -P\n/usr/sbin/php-fpm83 -F" > /etc/s6-overlay/s6-rc.d/php-fpm/run \
    && echo -e '#!/bin/execlineb -P\nnginx -g "daemon off;"' > /etc/s6-overlay/s6-rc.d/nginx/run \
    && echo -e '#!/bin/execlineb -P\nwith-contenv\n\nimportas -u PORT PORT\n\nif { echo\n"\n[INSTALL] 🚀 Starting app (:${PORT})\n\n" }\npython -m server' > /etc/s6-overlay/s6-rc.d/netalertx/run

# Set up s6 overlay dependencies
RUN touch /etc/s6-overlay/s6-rc.d/user/contents.d/SetupOneshot \
    && touch /etc/s6-overlay/s6-rc.d/user/contents.d/crond \
    && touch /etc/s6-overlay/s6-rc.d/user/contents.d/php-fpm \
    && touch /etc/s6-overlay/s6-rc.d/user/contents.d/nginx \
    && touch /etc/s6-overlay/s6-rc.d/user/contents.d/netalertx \
    && touch /etc/s6-overlay/s6-rc.d/crond/dependencies.d/SetupOneshot \
    && touch /etc/s6-overlay/s6-rc.d/php-fpm/dependencies.d/SetupOneshot \
    && touch /etc/s6-overlay/s6-rc.d/nginx/dependencies.d/SetupOneshot \
    && touch /etc/s6-overlay/s6-rc.d/nginx/dependencies.d/php-fpm \
    && touch /etc/s6-overlay/s6-rc.d/netalertx/dependencies.d/SetupOneshot \
    && touch /etc/s6-overlay/s6-rc.d/netalertx/dependencies.d/nginx

# Set permissions for application directories
RUN chown -R nginx:www-data ${INSTALL_DIR} \
    && chmod 750 ${INSTALL_DIR}/config ${INSTALL_DIR}/log ${INSTALL_DIR}/db \
    && find ${INSTALL_DIR}/config ${INSTALL_DIR}/log ${INSTALL_DIR}/db -type f -exec chmod 640 {} \; \
    && chown nginx:nginx /run/nginx/ /var/log/nginx/ /var/lib/nginx/ /var/lib/nginx/tmp/ \
    && chgrp www-data /var/www/localhost/htdocs/

# Create buildtimestamp.txt
RUN date +%s > ${INSTALL_DIR}/front/buildtimestamp.txt

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

ENTRYPOINT ["/init"]
