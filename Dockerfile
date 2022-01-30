FROM alpine

RUN apk add --no-cache cronie lighttpd php php-cgi php-fpm php-sqlite3 php-json sqlite python3 sudo curl perl perl-lwp-useragent-determined bind-tools git nmap \
    && apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing arp-scan \
    && git clone --depth=1 https://github.com/cjd/Pi.Alert /pialert \
    && sed -i 's/var\/www\/localhost/pialert\/front/g' /etc/lighttpd/lighttpd.conf \
    && sed -i 's/^.*server.port.*$/server.port = 20211/g' /etc/lighttpd/lighttpd.conf \
    && sed -i -r 's#\#.*server.event-handler = "linux-sysepoll".*#server.event-handler = "linux-sysepoll"#g' /etc/lighttpd/lighttpd.conf \
    && sed -i 's/~\/pialert/\/pialert/g' /pialert/install/pialert.cron \
    && sed -i 's/python/python3/g' /pialert/install/pialert.cron \
    && sed -i 's/env python$/env python3/g' /pialert/back/pialert.py \
    && sed -i 's/\/home\/pi//g' /pialert/config/pialert.conf \
    && (crontab -l 2>/dev/null; cat /pialert/install/pialert.cron) | crontab - \
    && sed -i -r 's#\#.*mod_alias.*,.*#    "mod_alias",#g' /etc/lighttpd/lighttpd.conf \
    && sed -i -r 's#.*include "mod_cgi.conf".*#   include "mod_cgi.conf"#g' /etc/lighttpd/lighttpd.conf \
    && sed -i -r 's#.*include "mod_fastcgi.conf".*#\#   include "mod_fastcgi.conf"#g' /etc/lighttpd/lighttpd.conf \
    && sed -i -r 's#.*include "mod_fastcgi_fpm.conf".*#   include "mod_fastcgi_fpm.conf"#g' /etc/lighttpd/lighttpd.conf \
    && sed -i -r 's|^.*listen =.*|listen = /var/run/php-fpm7/php7-fpm.sock|g' /etc/php*/php-fpm.d/www.conf \
    && sed -i -r 's|^.*listen.owner = .*|listen.owner = lighttpd|g' /etc/php*/php-fpm.d/www.conf \
    && sed -i -r 's|^.*listen.group = .*|listen.group = lighttpd|g' /etc/php*/php-fpm.d/www.conf \
    && sed -i -r 's|^.*listen.mode = .*|listen.mode = 0660|g' /etc/php*/php-fpm.d/www.conf \
    && sed -i -r 's|^server.document-root.*$|server.document-root = var.basedir|g' /etc/lighttpd/lighttpd.conf \
    && mkdir -p mkdir /var/run/php-fpm7 \
    && mkdir /usr/share/ieee-data \
    && python3 /pialert/back/pialert.py update_vendors

RUN { \
echo 'server.modules += ( "mod_fastcgi" )'; \
echo 'index-file.names += ( "index.php" )'; \
echo 'fastcgi.server = ('; \
echo '    ".php" => ('; \
echo '      "localhost" => ('; \
echo '        "socket"                => "/var/run/php-fpm7/php7-fpm.sock",'; \
echo '        "broken-scriptfilename" => "enable"'; \
echo '      ))'; \
echo ')'; \
} > /etc/lighttpd/mod_fastcgi_fpm.conf

# Expose the below port
EXPOSE 20211

CMD /usr/sbin/lighttpd -f /etc/lighttpd/lighttpd.conf & /usr/sbin/php-fpm7 & crond -n
