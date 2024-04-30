FROM alpine:3.19 as builder

ARG INSTALL_DIR=/app

ENV PYTHONUNBUFFERED 1

RUN apk add --no-cache bash python3 \
    && python -m venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . ${INSTALL_DIR}/

RUN pip install requests paho-mqtt scapy cron-converter pytz json2table dhcp-leases pyunifi speedtest-cli chardet dnspython\
    && bash -c "find ${INSTALL_DIR} -type d -exec chmod 750 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f -exec chmod 640 {} \;" \
    && bash -c "find ${INSTALL_DIR} -type f \( -name '*.sh' -o -name '*.py' -o -name 'pialert-cli' -o -name 'speedtest-cli' \) -exec chmod 750 {} \;"

# second stage
FROM alpine:3.19 as runner

ARG INSTALL_DIR=/app

COPY --from=builder /opt/venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH" 

# default port and listen address
ENV PORT=20211 LISTEN_ADDR=0.0.0.0 

# needed for s6-overlay
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

# ❗ IMPORTANT - if you modify this file modify the /install/install_dependecies.sh file as well ❗ 

RUN apk update --no-cache \
    && apk add --no-cache bash zip lsblk gettext-envsubst sudo mtr tzdata s6-overlay \
    && apk add --no-cache curl arp-scan iproute2 iproute2-ss nmap nmap-scripts traceroute net-tools net-snmp-tools bind-tools awake ca-certificates \
    && apk add --no-cache sqlite php82 php82-fpm php82-cgi php82-curl php82-sqlite3 php82-session \
    && apk add --no-cache python3 nginx \
    && ln -s /usr/bin/awake /usr/bin/wakeonlan \
    && bash -c "install -d -m 750 -o nginx -g www-data ${INSTALL_DIR} ${INSTALL_DIR}" \
    && rm -f /etc/nginx/http.d/default.conf

COPY --from=builder --chown=nginx:www-data ${INSTALL_DIR}/ ${INSTALL_DIR}/

RUN ${INSTALL_DIR}/dockerfiles/pre-setup.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=2 \
  CMD curl -sf -o /dev/null ${LISTEN_ADDR}:${PORT}/api/app_state.json

ENTRYPOINT ["/init"]
