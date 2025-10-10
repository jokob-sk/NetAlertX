FROM alpine:3.22 AS builder

ARG INSTALL_DIR=/app

ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apk add --no-cache bash shadow python3 python3-dev gcc musl-dev libffi-dev openssl-dev git \
    && python -m venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . ${INSTALL_DIR}/

RUN pip install openwrt-luci-rpc asusrouter asyncio aiohttp graphene flask flask-cors unifi-sm-api tplink-omada-client wakeonlan pycryptodome requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet python-nmap dnspython librouteros yattag zeroconf git+https://github.com/foreign-sub/aiofreepybox.git \
    && bash -c "find ${INSTALL_DIR} -type d -exec chmod 750 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f -exec chmod 640 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f \( -name '*.sh' -o -name '*.py'  -o -name 'speedtest-cli' \) -exec chmod 750 {} \;"

# Append Iliadbox certificate to aiofreepybox
RUN cat ${INSTALL_DIR}/install/freebox_certificate.pem >> /opt/venv/lib/python3.12/site-packages/aiofreepybox/freebox_certificates.pem

# second stage
FROM alpine:3.22 AS runner

ARG INSTALL_DIR=/app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/sbin/usermod /usr/sbin/groupmod /usr/sbin/

# Enable venv
ENV PATH="/opt/venv/bin:$PATH" 

# default port and listen address
ENV PORT=20211 LISTEN_ADDR=0.0.0.0 

# needed for s6-overlay
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

# ❗ IMPORTANT - if you modify this file modify the /install/install_dependecies.sh file as well ❗ 

RUN apk update --no-cache \
    && apk add --no-cache bash libbsd zip lsblk gettext-envsubst sudo mtr tzdata s6-overlay \
    && apk add --no-cache curl arp-scan iproute2 iproute2-ss nmap nmap-scripts traceroute nbtscan net-tools net-snmp-tools bind-tools awake ca-certificates \
    && apk add --no-cache sqlite php83 php83-fpm php83-cgi php83-curl php83-sqlite3 php83-session \
    && apk add --no-cache python3 nginx \
    && ln -s /usr/bin/awake /usr/bin/wakeonlan \
    && bash -c "install -d -m 750 -o nginx -g www-data ${INSTALL_DIR} ${INSTALL_DIR}" \
    && rm -f /etc/nginx/http.d/default.conf

COPY --from=builder --chown=nginx:www-data ${INSTALL_DIR}/ ${INSTALL_DIR}/

# Add crontab file
COPY --chmod=600 --chown=root:root install/crontab /etc/crontabs/root

# Start all required services
RUN ${INSTALL_DIR}/dockerfiles/start.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=2 \
    CMD curl -sf -o /dev/null ${LISTEN_ADDR}:${PORT}/php/server/query_json.php?file=app_state.json

ENTRYPOINT ["/init"]
