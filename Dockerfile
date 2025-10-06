FROM alpine:3.22 AS builder

ARG INSTALL_DIR=/app

ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apk add --no-cache bash shadow python3 python3-dev gcc musl-dev libffi-dev openssl-dev git \
    && python -m venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install openwrt-luci-rpc asusrouter asyncio aiohttp graphene flask flask-cors unifi-sm-api tplink-omada-client wakeonlan pycryptodome requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet python-nmap dnspython librouteros yattag zeroconf simplejson future six urllib3 httplib2 git+https://github.com/foreign-sub/aiofreepybox.git

RUN chmod -R u-rwx,g-rwx /opt

# second stage is the main runtime stage with just the minimum required to run the application
# The runner is used for both devcontainer, and as a base for the hardened stage.
FROM alpine:3.22 AS runner

ARG INSTALL_DIR=/app

ENV PATH="/opt/venv/bin:/usr/bin:/sbin:/bin:$PATH" 

# NetAlertX app directories
ENV NETALERTX_APP=${INSTALL_DIR}
ENV NETALERTX_CONFIG=${NETALERTX_APP}/config
ENV NETALERTX_FRONT=${NETALERTX_APP}/front
ENV NETALERTX_SERVER=${NETALERTX_APP}/server
ENV NETALERTX_API=${NETALERTX_APP}/api
ENV NETALERTX_DB=${NETALERTX_APP}/db
ENV NETALERTX_DB_FILE=${NETALERTX_DB}/app.db
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
ENV LOG_CROND=${NETALERTX_LOG}/crond.log

# System Services configuration files
ENV SYSTEM_SERVICES=/services
ENV SYSTEM_SERVICES_CONFIG=${SYSTEM_SERVICES}/config
ENV SYSTEM_NGINIX_CONFIG=${SYSTEM_SERVICES_CONFIG}/nginx
ENV SYSTEM_NGINX_CONFIG_FILE=${SYSTEM_NGINIX_CONFIG}/nginx.conf
ENV NETALERTX_CONFIG_FILE=${NETALERTX_CONFIG}/app.conf
ENV SYSTEM_SERVICES_PHP_FOLDER=${SYSTEM_SERVICES_CONFIG}/php
ENV SYSTEM_SERVICES_PHP_FPM_D=${SYSTEM_SERVICES_PHP_FOLDER}/php-fpm.d
ENV SYSTEM_SERVICES_CROND=${SYSTEM_SERVICES_CONFIG}/crond
ENV SYSTEM_SERVICES_RUN=${SYSTEM_SERVICES}/run
ENV SYSTEM_SERVICES_RUN_TMP=${SYSTEM_SERVICES_RUN}/tmp
ENV SYSTEM_SERVICES_RUN_LOG=${SYSTEM_SERVICES_RUN}/logs
ENV PHP_FPM_CONFIG_FILE=${SYSTEM_SERVICES_PHP_FOLDER}/php-fpm.conf

ENV PYTHONPATH=${NETALERTX_SERVER}
ENV PYTHONUNBUFFERED=1 


RUN apk add --no-cache bash mtr libbsd zip lsblk sudo tzdata curl arp-scan iproute2 \
    iproute2-ss nmap nmap-scripts traceroute nbtscan net-tools net-snmp-tools bind-tools awake \
    ca-certificates sqlite php83 php83-fpm php83-cgi php83-curl php83-sqlite3 php83-session python3 \
    envsubst nginx sudo shadow && \
    rm -Rf /var/cache/apk/*  && \
    rm -Rf /etc/nginx && \
    addgroup -g 20211 netalertx && \
    adduser -u 20211 -D -h ${NETALERTX_APP} -G netalertx netalertx && \
    apk del shadow



# Install application, copy files, set permissions
COPY --from=builder --chown=20212:20212 /opt/venv /opt/venv
COPY --from=builder /usr/sbin/usermod /usr/sbin/groupmod /usr/sbin/
COPY --chown=netalertx:netalertx install/production-filesystem/ /
COPY --chown=netalertx:netalertx --chmod=755 back ${NETALERTX_BACK}
COPY --chown=netalertx:netalertx --chmod=755 front ${NETALERTX_FRONT}
COPY --chown=netalertx:netalertx --chmod=755 server ${NETALERTX_SERVER}
RUN install -d -o netalertx -g netalertx -m 755 ${NETALERTX_API}  \
    ${NETALERTX_LOG} ${SYSTEM_SERVICES_RUN_TMP} ${SYSTEM_SERVICES_RUN_LOG} && \
    sh -c "find ${NETALERTX_APP} -type f \( -name '*.sh' -o -name 'speedtest-cli' \) \
    -exec chmod 750 {} \;"


#initialize each service with the dockerfiles/init-*.sh scripts, once.
RUN apk add libcap && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/nmap && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/arp-scan && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/traceroute && \
    setcap cap_net_raw,cap_net_admin+eip /opt/venv/bin/scapy && \
    /bin/sh /build/init-nginx.sh && \
    /bin/sh /build/init-php-fpm.sh && \
    /bin/sh /build/init-crond.sh && \
    /bin/sh /build/init-backend.sh && \
    chmod 755 ${NETALERTX_BACK}/update_vendors.sh ${NETALERTX_BACK}/cron_script.sh ${NETALERTX_BACK}/speedtest-cli && \
    rm -rf /build && \
    apk del libcap
# set netalertx to allow sudoers for any command, no password
RUN echo "netalertx ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

ENTRYPOINT ["/bin/sh","-c","sleep infinity"]

# Final hardened stage to improve security by setting least possible permissions and removing sudo access.
# When complete, if the image is compromised, there's not much that can be done with it.
# This stage is separate from Runner stage so that devcontainer can use the Runner stage.
FROM runner AS hardened

# create readonly user and group with no shell access.
# Readonly user marks folders that are created by NetAlertX, but should not be modified.
RUN addgroup -g 20212 readonly && \
    adduser -u 20212 -G readonly -D -h /app readonly && \
    usermod -s /sbin/nologin readonly


# reduce permissions to minimum necessary for all NetAlertX files and folders

RUN chown -R readonly:readonly ${NETALERTX_BACK} ${NETALERTX_FRONT} ${NETALERTX_SERVER} ${SYSTEM_SERVICES} ${SYSTEM_SERVICES} && \
    chmod -R 004 ${NETALERTX_BACK} ${NETALERTX_FRONT} ${NETALERTX_SERVER} && \
    find ${NETALERTX_BACK} ${NETALERTX_FRONT} ${NETALERTX_SERVER} -type d -exec chmod 005 {} + && \
    chmod -R 005 ${SYSTEM_SERVICES} ${SYSTEM_SERVICES}/* && \
    chown -R netalertx:netalertx ${NETALERTX_CONFIG} ${NETALERTX_DB} ${NETALERTX_API} ${NETALERTX_LOG} && \
    chmod -R 600 ${NETALERTX_CONFIG} ${NETALERTX_DB} ${NETALERTX_API} ${NETALERTX_LOG} && \
    chmod 700 ${NETALERTX_CONFIG} ${NETALERTX_DB} ${NETALERTX_API} ${NETALERTX_LOG} ${NETALERTX_PLUGINS_LOG} ${SYSTEM_SERVICES_RUN_TMP} && \
    chown readonly:readonly /entrypoint.sh && \
    install -d -o netalertx -g netalertx -m 700 ${SYSTEM_SERVICES_RUN} ${SYSTEM_SERVICES_RUN_TMP} ${SYSTEM_SERVICES_RUN_LOG} && \
    chmod 005 /entrypoint.sh ${NETALERTX_BACK}/update_vendors.sh ${NETALERTX_BACK}/cron_script.sh ${NETALERTX_BACK}/speedtest-cli 

#
# remove sudo and alpine installers pacakges
RUN apk del sudo apk-tools && \
    rm -rf /var/cache/apk/* 
# remove all users and groups except readonly and netalertx & remove all sudoers
RUN rm -Rf /etc/sudoers.d/* /etc/shadow /etc/gshadow /etc/sudoers \
    /lib/apk /lib/firmware  /lib/modules-load.d /lib/sysctl.d /mnt /home/ /root \
    /srv /media && \
    sed -i -n -e '/^readonly:/p' -e '/^netalertx:/p' /etc/passwd && \
    sed -i -n -e '/^readonly:/p' -e '/^netalertx:/p' /etc/group && \
    echo -ne '#!/bin/sh\n"$@"\n' > /usr/bin/sudo && chmod +x /usr/bin/sudo




USER netalertx

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /services/healthcheck.sh

#ENTRYPOINT [ "/bin/sh" ]
ENTRYPOINT [ "/bin/sh", "/entrypoint.sh" ]
