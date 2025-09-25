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
COPY front ${INSTALL_DIR}/front
COPY server ${INSTALL_DIR}/server

RUN pip install openwrt-luci-rpc asusrouter asyncio aiohttp graphene flask flask-cors unifi-sm-api tplink-omada-client wakeonlan pycryptodome requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet python-nmap dnspython librouteros yattag git+https://github.com/foreign-sub/aiofreepybox.git

RUN bash -c "find ${INSTALL_DIR} -type d -exec chmod 750 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f -exec chmod 640 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f \( -name '*.sh' -o -name '*.py'  -o -name 'speedtest-cli' \) -exec chmod 750 {} \;"

# second stage
FROM alpine:3.22 AS runner

RUN addgroup -g 20211 netalertx && \
    adduser -u 20211 -G netalertx -D -h /app netalertx && \
    addgroup -g 20212 readonly && \
    adduser -u 20212 -G readonly -D -h /app readonly

ARG INSTALL_DIR=/app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/sbin/usermod /usr/sbin/groupmod /usr/sbin/

COPY install/alpine-docker/ /

# Enable venv
ENV PATH="/opt/venv/bin:$PATH" 



ENV PORT=20211 LISTEN_ADDR=0.0.0.0 GRAPHQL_PORT=20212
# NetAlertX app directories
ENV NETALERTX_APP=${INSTALL_DIR}
ENV NETALERTX_CONFIG=${NETALERTX_APP}/config
ENV NETALERTX_FRONT=${NETALERTX_APP}/front
ENV NETALERTX_SERVER=${NETALERTX_APP}/server
ENV NETALERTX_API=${NETALERTX_APP}/api
ENV NETALERTX_DB=${NETALERTX_APP}/db
ENV NETALERTX_BACK=${NETALERTX_APP}/back
ENV NETALERTX_LOG=${NETALERTX_APP}/log
ENV NETALERTX_PLUGINS_LOG=${NETALERTX_LOG}/plugins
ENV NETALERTX_NGINIX_CONFIG=${NETALERTX_APP}/services/nginx

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
ENV LOG_CROND=${NETALERTX_LOG}/crond.log

# Important configuration files
ENV NGINX_CONFIG_FILE=${NETALERTX_NGINIX_CONFIG}/nginx.conf
ENV NETALERTX_CONFIG_FILE=${NETALERTX_CONFIG}/app.conf
ENV NETALERTX_DB_FILE=${NETALERTX_DB}/app.db
ENV PHP_FPM_CONFIG_FILE=/etc/php83/php-fpm.conf
ENV PHP_WWW_CONF_FILE=/etc/php83/php-fpm.d/www.conf


RUN apk update --no-cache \
    && apk add --no-cache bash libbsd zip lsblk gettext-envsubst sudo mtr tzdata \
    && apk add --no-cache curl arp-scan iproute2 iproute2-ss nmap nmap-scripts traceroute nbtscan avahi avahi-tools openrc dbus net-tools net-snmp-tools bind-tools awake ca-certificates \
    && apk add --no-cache sqlite php83 php83-fpm php83-cgi php83-curl php83-sqlite3 php83-session \
    && apk add --no-cache python3 nginx


COPY --from=builder --chown=readonly:readonly ${INSTALL_DIR}/ ${INSTALL_DIR}/
# set this properly to handle recursive ownership changes
RUN ln -s /usr/bin/awake /usr/bin/wakeonlan \
    && rm -f /etc/nginx/http.d/default.conf


# Create required directories
RUN mkdir -p ${INSTALL_DIR}/config ${INSTALL_DIR}/db ${INSTALL_DIR}/log/plugins



# Create empty log files and API files
RUN touch ${LOG_APP} \
    && touch ${LOG_EXECUTION_QUEUE} \
    && touch ${LOG_APP_FRONT} \
    && touch ${LOG_APP_PHP_ERRORS} \
    && touch ${LOG_STDERR} \
    && touch ${LOG_STDOUT} \
    && touch ${LOG_DB_IS_LOCKED} \
    && touch ${LOG_IP_CHANGES} \
    && touch ${LOG_REPORT_OUTPUT_TXT} \
    && touch ${LOG_REPORT_OUTPUT_HTML} \
    && touch ${LOG_REPORT_OUTPUT_JSON} \
    && touch ${NETALERTX_API}/user_notifications.json \
    && chown -R netalertx:netalertx ${NETALERTX_LOG} ${NETALERTX_API}

# Setup services
RUN mkdir -p /services




#initialize each service with the dockerfiles/init-*.sh scripts, once.
RUN chmod +x /build/*.sh \
    && /build/init-nginx.sh \
    && /build/init-php-fpm.sh \
    && /build/init-crond.sh \
    && /build/init-backend.sh \
    && rm -rf /build/*

# Create buildtimestamp.txt

RUN chmod +x /services/*.sh /entrypoint.sh


RUN date +%s > ${INSTALL_DIR}/front/buildtimestamp.txt

# Ensure proper permissions
# Skip certain system directories to avoid permission issues
# Also skip log directories to avoid changing log file ownerships
RUN find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o -path /run -prune -o -path /var/log -prune -o -path /tmp -prune -o -group 0 -o -user 0 -exec chown readonly:readonly {} +
RUN chmod 555 /app
RUN chown -R readonly:readonly ${NETALERTX_BACK} ${NETALERTX_FRONT} ${NETALERTX_SERVER} ${NETALERTX_APP}/services
RUN chmod -R 004 ${NETALERTX_BACK} ${NETALERTX_FRONT} ${NETALERTX_SERVER} ${NETALERTX_APP}/services
RUN chown -R netalertx:netalertx ${INSTALL_DIR}/config ${INSTALL_DIR}/db ${INSTALL_DIR}/log ${INSTALL_DIR}/api
RUN find ${NETALERTX_APP} -type d -exec chmod 555 {} \;
RUN cp ${NETALERTX_BACK}/app.conf ${NETALERTX_CONFIG}/app.conf && \
    cp ${NETALERTX_BACK}/app.db ${NETALERTX_DB}/app.db && \
    chmod 600 ${NETALERTX_CONFIG}/app.conf && \
    chmod 600 ${NETALERTX_DB}/app.db
RUN chmod -R 700 ${NETALERTX_CONFIG} ${NETALERTX_DB} ${NETALERTX_LOG} ${NETALERTX_API}
RUN find ${NETALERTX_CONFIG} ${NETALERTX_DB} ${NETALERTX_LOG} ${NETALERTX_API} -type f -exec chmod 600 {} \;
RUN chmod -R 555 /services
RUN chown readonly:readonly /
RUN rm /usr/bin/sudo
RUN touch /var/log/nginx/access.log /var/log/nginx/error.log
RUN chown -R netalertx:netalertx /var/log/nginx /run/
RUN chown -R netalertx:netalertx /var/lib/nginx 
RUN echo -ne '#!/bin/bash\nexit 0\n' > /usr/bin/sudo && chmod +x /usr/bin/sudo



USER netalertx

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

CMD /entrypoint.sh

# Assistant, I commented this out while bringing up permissions. this way I can login by specifying the command.
# ok? got it?  We're using CMD now instead of ENTRYPOINT so we can override it if needed. Stop specifying the entrypoint.
# 
# ENTRYPOINT ["/entrypoint.sh"]


