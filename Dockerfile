FROM debian:buster-slim

ARG dir="/home/pi/pialert"

#Update and reduce image size
RUN apt-get update \
    && apt-get install --no-install-recommends apt-utils cron sudo lighttpd php php-cgi php-fpm php-sqlite3 sqlite3 dnsutils net-tools python iproute2 -y \
    #Install without the --no-install-recommends flag
    && apt-get install curl arp-scan -y \
    #clean-up
    && apt clean autoclean \
    && apt autoremove 

#add the pi user
RUN useradd -ms /bin/bash pi 
WORKDIR /home/pi

# Lighttpd & PHP
RUN mv /var/www/html/index.lighttpd.html /var/www/html/index.lighttpd.html.old \
    && ln -s $dir/install/index.html /var/www/html/index.html \
    && lighttpd-enable-mod fastcgi-php 

COPY . $dir

# delete .git/ files and the tar/ realese directory to make the image smaller
#RUN rm -r $dir/.git \
RUN rm -r $dir/tar 

# Pi.Alert   
RUN ln -s $dir/front /var/www/html/pialert  \
    && python $dir/back/pialert.py update_vendors \    
    && (crontab -l 2>/dev/null; cat $dir/install/pialert.cron) | crontab - \
    && chgrp -R www-data $dir/db \
    && chmod -R 770 $dir/db \
    # changing the default port number 80 to something random, here 20211
    && sed -ie 's/= 80/= 20211/g' /etc/lighttpd/lighttpd.conf \
    && service lighttpd restart 

# Expose the below port
EXPOSE 20211

# Set up startup script to run two commands, cron and the lighttpd server
# RUN chmod +x $dir/dockerfiles/start.sh

CMD ["/home/pi/pialert/dockerfiles/start.sh"]
