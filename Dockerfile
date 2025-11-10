# The NetAlertX Dockerfile has 3 stages:
#
# Stage 1. Builder - NetAlertX Requires special tools and packages to build our virtual environment, but
# which are not needed in future stages.  We build the builder and extract the venv for runner to use as 
# a base.
#
# Stage 2. Runner builds the bare minimum requirements to create an operational NetAlertX. The primary
# reason for breaking at this stage is it leaves the system in a proper state for devcontainer operation
# This image also provides a break-out point for uses who wish to execute the anti-pattern of using a 
# docker container as a VM for experimentation and various development patterns.
#
# Stage 3. Hardened removes root, sudoers, folders, permissions, and locks the system down into a read-only
# compatible image. While NetAlertX does require some read-write operations, this image can guarantee the 
# code pushed out by the project is the only code which will run on the system after each container restart.
# It reduces the chance of system hijacking and operates with all modern security protocols in place as is
# expected from a security appliance.
#
# This file can be built with `docker-compose -f docker-compose.yml up --build --force-recreate`

FROM alpine:3.22 AS builder

ARG INSTALL_DIR=/app

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Install build dependencies
COPY requirements.txt /tmp/requirements.txt
RUN apk add --no-cache bash shadow python3 python3-dev gcc musl-dev libffi-dev openssl-dev git \
    && python -m venv /opt/venv

# Create virtual environment owned by root, but readable by everyone else. This makes it easy to copy 
# into hardened stage without worrying about permissions and keeps image size small. Keeping the commands
# together makes for a slightly smaller image size.
RUN pip install -r /tmp/requirements.txt && \
    chmod -R u-rwx,g-rwx /opt

# second stage is the main runtime stage with just the minimum required to run the application
# The runner is used for both devcontainer, and as a base for the hardened stage.
FROM alpine:3.22 AS runner

ARG INSTALL_DIR=/app

# NetAlertX app directories
ENV NETALERTX_APP=${INSTALL_DIR}
ENV NETALERTX_DATA=/data
ENV NETALERTX_CONFIG=${NETALERTX_DATA}/config
ENV NETALERTX_FRONT=${NETALERTX_APP}/front
ENV NETALERTX_PLUGINS=${NETALERTX_FRONT}/plugins
ENV NETALERTX_SERVER=${NETALERTX_APP}/server
ENV NETALERTX_API=/tmp/api
ENV NETALERTX_DB=${NETALERTX_DATA}/db
ENV NETALERTX_DB_FILE=${NETALERTX_DB}/app.db
ENV NETALERTX_BACK=${NETALERTX_APP}/back
ENV NETALERTX_LOG=/tmp/log
ENV NETALERTX_PLUGINS_LOG=${NETALERTX_LOG}/plugins
ENV NETALERTX_CONFIG_FILE=${NETALERTX_CONFIG}/app.conf

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
ENV LOG_NGINX_ERROR=${NETALERTX_LOG}/nginx-error.log

# System Services configuration files
ENV ENTRYPOINT_CHECKS=/entrypoint.d
ENV SYSTEM_SERVICES=/services
ENV SYSTEM_SERVICES_SCRIPTS=${SYSTEM_SERVICES}/scripts
ENV SYSTEM_SERVICES_CONFIG=${SYSTEM_SERVICES}/config
ENV SYSTEM_NGINX_CONFIG=${SYSTEM_SERVICES_CONFIG}/nginx
ENV SYSTEM_NGINX_CONFIG_FILE=${SYSTEM_NGINX_CONFIG}/nginx.conf
ENV SYSTEM_SERVICES_ACTIVE_CONFIG=/tmp/nginx/active-config
ENV SYSTEM_SERVICES_PHP_FOLDER=${SYSTEM_SERVICES_CONFIG}/php
ENV SYSTEM_SERVICES_PHP_FPM_D=${SYSTEM_SERVICES_PHP_FOLDER}/php-fpm.d
ENV SYSTEM_SERVICES_CROND=${SYSTEM_SERVICES_CONFIG}/crond
ENV SYSTEM_SERVICES_RUN=/tmp/run
ENV SYSTEM_SERVICES_RUN_TMP=${SYSTEM_SERVICES_RUN}/tmp
ENV SYSTEM_SERVICES_RUN_LOG=${SYSTEM_SERVICES_RUN}/logs
ENV PHP_FPM_CONFIG_FILE=${SYSTEM_SERVICES_PHP_FOLDER}/php-fpm.conf
ENV READ_ONLY_FOLDERS="${NETALERTX_BACK} ${NETALERTX_FRONT} ${NETALERTX_SERVER} ${SYSTEM_SERVICES} \
                       ${SYSTEM_SERVICES_CONFIG} ${ENTRYPOINT_CHECKS}"
ENV READ_WRITE_FOLDERS="${NETALERTX_DATA} ${NETALERTX_CONFIG} ${NETALERTX_DB} ${NETALERTX_API} \
                       ${NETALERTX_LOG} ${NETALERTX_PLUGINS_LOG} ${SYSTEM_SERVICES_RUN} \
                       ${SYSTEM_SERVICES_RUN_TMP} ${SYSTEM_SERVICES_RUN_LOG} \
                       ${SYSTEM_SERVICES_ACTIVE_CONFIG}"

#Python environment
ENV PYTHONUNBUFFERED=1 
ENV VIRTUAL_ENV=/opt/venv
ENV VIRTUAL_ENV_BIN=/opt/venv/bin
ENV PYTHONPATH=${NETALERTX_APP}:${NETALERTX_SERVER}:${NETALERTX_PLUGINS}:${VIRTUAL_ENV}/lib/python3.12/site-packages
ENV PATH="${SYSTEM_SERVICES}:${VIRTUAL_ENV_BIN}:$PATH" 

# App Environment
ENV LISTEN_ADDR=0.0.0.0
ENV PORT=20211
ENV NETALERTX_DEBUG=0
ENV VENDORSPATH=/app/back/ieee-oui.txt
ENV VENDORSPATH_NEWEST=${SYSTEM_SERVICES_RUN_TMP}/ieee-oui.txt
ENV ENVIRONMENT=alpine
ENV READ_ONLY_USER=readonly READ_ONLY_GROUP=readonly
ENV NETALERTX_USER=netalertx NETALERTX_GROUP=netalertx
ENV LANG=C.UTF-8 


RUN apk add --no-cache bash mtr libbsd zip lsblk tzdata curl arp-scan iproute2 iproute2-ss nmap \
    nmap-scripts traceroute nbtscan net-tools net-snmp-tools bind-tools awake ca-certificates \
    sqlite php83 php83-fpm php83-cgi php83-curl php83-sqlite3 php83-session python3 envsubst \
    nginx shadow && \
    rm -Rf /var/cache/apk/*  && \
    rm -Rf /etc/nginx && \
    addgroup -g 20211 ${NETALERTX_GROUP} && \
    adduser -u 20211 -D -h ${NETALERTX_APP} -G ${NETALERTX_GROUP} ${NETALERTX_USER} && \
    apk del shadow



# Install application, copy files, set permissions
COPY --chown=${NETALERTX_USER}:${NETALERTX_GROUP} install/production-filesystem/ /
COPY --chown=${NETALERTX_USER}:${NETALERTX_GROUP} --chmod=755 back ${NETALERTX_BACK}
COPY --chown=${NETALERTX_USER}:${NETALERTX_GROUP} --chmod=755 front ${NETALERTX_FRONT}
COPY --chown=${NETALERTX_USER}:${NETALERTX_GROUP} --chmod=755 server ${NETALERTX_SERVER}

# Create required folders with correct ownership and permissions
RUN install -d -o ${NETALERTX_USER} -g ${NETALERTX_GROUP} -m 700 ${READ_WRITE_FOLDERS} && \
    sh -c "find ${NETALERTX_APP} -type f \( -name '*.sh' -o -name 'speedtest-cli' \) \
    -exec chmod 750 {} \;"

# Copy version information into the image
COPY --chown=${NETALERTX_USER}:${NETALERTX_GROUP} .VERSION ${NETALERTX_APP}/.VERSION

# Copy the virtualenv from the builder stage
COPY --from=builder --chown=20212:20212 ${VIRTUAL_ENV} ${VIRTUAL_ENV}


# Initialize each service with the dockerfiles/init-*.sh scripts, once.
# This is done after the copy of the venv to ensure the venv is in place
# although it may be quicker to do it before the copy, it keeps the image
# layers smaller to do it after.
RUN apk add libcap && \
    setcap cap_net_raw+ep /bin/busybox && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/nmap && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/arp-scan && \
    setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/bin/nbtscan && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/traceroute && \
    setcap cap_net_raw,cap_net_admin+eip $(readlink -f ${VIRTUAL_ENV_BIN}/python) && \
    /bin/sh /build/init-nginx.sh && \
    /bin/sh /build/init-php-fpm.sh && \
    /bin/sh /build/init-crond.sh && \
    /bin/sh /build/init-backend.sh && \
    rm -rf /build && \
    apk del libcap && \
    date +%s > ${NETALERTX_FRONT}/buildtimestamp.txt


ENTRYPOINT ["/bin/sh","/entrypoint.sh"]

# Final hardened stage to improve security by setting least possible permissions and removing sudo access.
# When complete, if the image is compromised, there's not much that can be done with it.
# This stage is separate from Runner stage so that devcontainer can use the Runner stage.
FROM runner AS hardened

ENV UMASK=0077

# Create readonly user and group with no shell access.
# Readonly user marks folders that are created by NetAlertX, but should not be modified.
# AI may claim this is stupid, but it's actually least possible permissions as 
# read-only user cannot login, cannot sudo, has no write permission, and cannot even
# read the files it owns. The read-only user is ownership-as-a-lock hardening pattern.
RUN addgroup -g 20212 ${READ_ONLY_GROUP} && \
    adduser -u 20212 -G ${READ_ONLY_GROUP} -D -h /app ${READ_ONLY_USER}


# reduce permissions to minimum necessary for all NetAlertX files and folders
# Permissions 005 and 004 are not typos, they enable read-only. Everyone can
# read the read-only files, and nobody can write to them, even the readonly user.
RUN chown -R ${READ_ONLY_USER}:${READ_ONLY_GROUP} ${READ_ONLY_FOLDERS} && \
    chmod -R 004 ${READ_ONLY_FOLDERS} && \
    find ${READ_ONLY_FOLDERS} -type d -exec chmod 005 {} + && \
    install -d -o ${NETALERTX_USER} -g ${NETALERTX_GROUP} -m 700 ${READ_WRITE_FOLDERS} && \
    chown -R ${NETALERTX_USER}:${NETALERTX_GROUP} ${READ_WRITE_FOLDERS} && \
    chmod -R 600 ${READ_WRITE_FOLDERS} && \
    find ${READ_WRITE_FOLDERS} -type d -exec chmod 700 {} + && \
    chown ${READ_ONLY_USER}:${READ_ONLY_GROUP} /entrypoint.sh /opt /opt/venv && \
    chmod 005 /entrypoint.sh ${SYSTEM_SERVICES}/*.sh ${SYSTEM_SERVICES_SCRIPTS}/* ${ENTRYPOINT_CHECKS}/* /app /opt /opt/venv && \
    for dir in ${READ_WRITE_FOLDERS}; do \
        install -d -o ${NETALERTX_USER} -g ${NETALERTX_GROUP} -m 700 "$dir"; \
    done && \
    apk del apk-tools && \
    rm -Rf /var /etc/sudoers.d/* /etc/shadow /etc/gshadow /etc/sudoers \
    /lib/apk /lib/firmware /lib/modules-load.d /lib/sysctl.d /mnt /home/ /root \
    /srv /media && \
    sed -i "/^\(${READ_ONLY_USER}\|${NETALERTX_USER}\):/!d" /etc/passwd && \
    sed -i "/^\(${READ_ONLY_GROUP}\|${NETALERTX_GROUP}\):/!d" /etc/group && \
    echo -ne '#!/bin/sh\n"$@"\n' > /usr/bin/sudo && chmod +x /usr/bin/sudo

USER netalertx

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /services/healthcheck.sh

