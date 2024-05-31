#!/bin/bash

export INSTALL_DIR=/app
export APP_NAME=netalertx

# php-fpm setup
install -d -o nginx -g www-data /run/php/
sed -i "/^;pid/c\pid = /run/php/php8.3-fpm.pid" /etc/php83/php-fpm.conf
sed -i "/^listen/c\listen = /run/php/php8.3-fpm.sock" /etc/php83/php-fpm.d/www.conf
sed -i "/^;listen.owner/c\listen.owner = nginx" /etc/php83/php-fpm.d/www.conf
sed -i "/^;listen.group/c\listen.group = www-data" /etc/php83/php-fpm.d/www.conf
sed -i "/^user/c\user = nginx" /etc/php83/php-fpm.d/www.conf
sed -i "/^group/c\group = www-data" /etc/php83/php-fpm.d/www.conf

# s6 overlay setup
mkdir -p /etc/s6-overlay/s6-rc.d/{SetupOneshot,php-fpm/dependencies.d,nginx/dependencies.d}
mkdir -p /etc/s6-overlay/s6-rc.d/{SetupOneshot,php-fpm/dependencies.d,nginx/dependencies.d,$APP_NAME/dependencies.d}
echo "oneshot" > /etc/s6-overlay/s6-rc.d/SetupOneshot/type
echo "longrun" > /etc/s6-overlay/s6-rc.d/php-fpm/type
echo "longrun" > /etc/s6-overlay/s6-rc.d/nginx/type
echo "longrun" > /etc/s6-overlay/s6-rc.d/$APP_NAME/type
echo -e "${INSTALL_DIR}/dockerfiles/setup.sh" > /etc/s6-overlay/s6-rc.d/SetupOneshot/up
echo -e "#!/bin/execlineb -P\n/usr/sbin/php-fpm83 -F" > /etc/s6-overlay/s6-rc.d/php-fpm/run
echo -e '#!/bin/execlineb -P\nnginx -g "daemon off;"' > /etc/s6-overlay/s6-rc.d/nginx/run
echo -e '#!/bin/execlineb -P
        with-contenv

        importas -u PORT PORT

        if { echo
        "
            [INSTALL] 🚀 Starting app (:${PORT})

        " }' > /etc/s6-overlay/s6-rc.d/$APP_NAME/run
echo -e "python ${INSTALL_DIR}/server" >> /etc/s6-overlay/s6-rc.d/$APP_NAME/run
touch /etc/s6-overlay/s6-rc.d/user/contents.d/{SetupOneshot,php-fpm,nginx} /etc/s6-overlay/s6-rc.d/{php-fpm,nginx}/dependencies.d/SetupOneshot
touch /etc/s6-overlay/s6-rc.d/user/contents.d/{SetupOneshot,php-fpm,nginx,$APP_NAME} /etc/s6-overlay/s6-rc.d/{php-fpm,nginx,$APP_NAME}/dependencies.d/SetupOneshot
touch /etc/s6-overlay/s6-rc.d/nginx/dependencies.d/php-fpm
touch /etc/s6-overlay/s6-rc.d/$APP_NAME/dependencies.d/nginx

rm -f $0
