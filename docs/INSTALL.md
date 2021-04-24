# Pi.Alert Installation Guide
<!--- --------------------------------------------------------------------- --->
Initially designed to run on a Raspberry PI, probably it can run on many other
Linux distributions.

Estimated time: 20'

### Dependencies
  | Dependency | Comments                                                 |
  | ---------- | -------------------------------------------------------- |
  | Lighttpd   | Probably works on other webservers / not tested          |
  | arp-scan   | Required for Scan Method 1                               |
  | Pi.hole    | Optional. Scan Method 2. Check devices doing DNS queries |
  | dnsmasq    | Optional. Scan Method 3. Check devices using DHCP server |
  | IEEE HW DB | Necessary to identified Device vendor                    |

## One-step Automated Install:
<!--- --------------------------------------------------------------------- --->
  #### `curl -sSL https://github.com/pucherot/Pi.Alert/raw/main/install/pialert_install.sh | bash`

## One-step Automated Update:
<!--- --------------------------------------------------------------------- --->
  #### `curl -sSL https://github.com/pucherot/Pi.Alert/raw/main/install/pialert_update.sh | bash`

## Uninstall process
<!--- --------------------------------------------------------------------- --->
  - [Unistall process](./UNINSTALL.md)

## Installation process (step by step)
<!--- --------------------------------------------------------------------- --->

### Raspberry Setup
<!--- --------------------------------------------------------------------- --->
1.1 - Install 'Raspberry Pi OS'
  - Instructions https://www.raspberrypi.org/documentation/installation/installing-images/
  - *Lite version (without Desktop) is enough for Pi.Alert*

1.2 - Activate ssh
  - Create a empty file with name 'ssh' in the boot partition of the SD

1.3 - Start the raspberry

1.4 - Login to the system with pi user
  ```
  user: pi
  password: raspberry
  ```

1.5 - Change the default password of pi user
  ```
  passwd
  ```

1.6 - Setup the basic configuration
  ```
  sudo raspi-config
  ```

1.7 - Optionally, configure a static IP in raspi-config

1.8 - Update the OS
  ```
  sudo apt-get update
  sudo apt-get upgrade
  sudo shutdown -r now
  ```


### Pi-hole Setup (optional)
<!--- --------------------------------------------------------------------- --->
2.1 - Links & Doc
  - https://pi-hole.net/
  - https://github.com/pi-hole/pi-hole
  - https://github.com/pi-hole/pi-hole/#one-step-automated-install

2.2 - Login to the system with pi user

2.3 - Install Pi-hole
  ```
  curl -sSL https://install.pi-hole.net | bash
  ```
  - Select "Install web admin interface"
  - Select "Install web server lighttpd"

2.4 - Configure Pi-hole admin password
  ```
  pihole -a -p PASSWORD
  ```

2.5 - Connect to web admin panel
  ```
  hostname -I
  ```
  or this one if have severals interfaces
  ```
  ip -o route get 1 | sed 's/^.*src \([^ ]*\).*$/\1/;q'
  ```
  
  - http://192.168.1.x/admin/
  - (*replace 192.168.1.x with your Raspberry IP*)

2.6 - Activate DHCP server
  - Pi-hole admin portal -> Settings -> DHCP -> Mark "DHCP server enabled"

2.7 - Add pi.alert DNS Record
  ```
  hostname -I
  ```
  or this one if have severals interfaces
  ```
  ip -o route get 1 | sed 's/^.*src \([^ ]*\).*$/\1/;q'
  ```

  - Pi-hole admin portal -> Local DNS -> DNS Records -> Add new domain /IP
    - pi.alert    192.168.1.x
    - (*replace 192.168.1.x with your Raspberry IP*)

2.8 - Deactivate your current DHCP Server (*usually at your router or AP*)

2.9 - Renew your computer IP to unsure you are using the new DHCP and DNS server
  - Windows: cmd -> ipconfig /renew
  - Linux: shell -> sudo dhclient -r; sudo dhclient
  - Mac: Apple menu -> System Preferences -> Network -> Select the network
    -> Advanced -> TCP/IP -> Renew DHCP Lease


### Lighttpd & PHP
<!--- --------------------------------------------------------------------- --->
If you have installed Pi.hole, lighttpd and PHP are already installed and this
block is not necessary

3.1 - Install apt-utils
  ```
  sudo apt-get install apt-utils -y
  ```

3.2 - Install lighttpd
  ```
  sudo apt-get install lighttpd -y
  ```

3.3 - If Pi.Alert will be the only site available in this webserver, you can
  redirect the default server page to pialert subfolder
  ```
  sudo mv /var/www/html/index.lighttpd.html /var/www/html/index.lighttpd.html.old
  sudo ln -s ~/pialert/install/index.html /var/www/html/index.html
  ```

3.4 - Install PHP
  ```
  sudo apt-get install php php-cgi php-fpm php-sqlite3 -y     
  ```

3.5 - Activate PHP
  ```
  sudo lighttpd-enable-mod fastcgi-php
  sudo service lighttpd restart
  ```

3.6 - Install sqlite3
  ```
  sudo apt-get install sqlite3 -y
  ```


### arp-scan & Python
<!--- --------------------------------------------------------------------- --->
4.1 - Install arp-scan utility and test
  ```
  sudo apt-get install arp-scan -y
  sudo arp-scan -l
  ```

4.2 - Install dnsutils & net-tools utilities
  ```
  sudo apt-get install dnsutils net-tools -y
  ```

4.3 - Test Python

  New versions of 'Raspberry Pi OS' includes Python. You can check that 
  Python is installed with the command:
  ```
  python -V
  ```

  New versions of Ubuntu includes Python 3. You can choose between use `python3`
  command or to install Python 2 (that includes `python` command).
  
  
  If you prefer to use Python 3, in the next installation block, you must update
  `pialert.cron` file with the correct command: `python3` instead of `python`.
  ```
  python3 -V
  ```

4.4 - If Python is not installed in your system, you can install it with this
  command:
  ```
  sudo apt-get install python
  ```
  Or this one if you prefer Python 3:
  ```
  sudo apt-get install python3
  ```

### Pi.Alert
<!--- --------------------------------------------------------------------- --->
5.1 - Download Pi.Alert and uncompress
  ```
  cd
  curl -LO https://github.com/pucherot/Pi.Alert/raw/main/tar/pialert_latest.tar
  tar xvf pialert_latest.tar
  rm pialert_latest.tar
  ```

5.2 - Public the front portal
  ```
  sudo ln -s ~/pialert/front /var/www/html/pialert
  ```

5.3 - Configure web server redirection

  If you have configured your DNS server (Pi.hole or other) to resolve pi.alert
  with the IP of your raspberry, youy must configure lighttpd to redirect these 
  requests to the correct pialert web folder
  ```
  sudo cp ~/pialert/install/pialert_front.conf /etc/lighttpd/conf-available
  sudo ln -s ../conf-available/pialert_front.conf /etc/lighttpd/conf-enabled/pialert_front.conf
  sudo /etc/init.d/lighttpd restart
  ```

5.4 - If you want to use email reporting with gmail
  - Go to your Google Account https://myaccount.google.com/
  - On the left navigation panel, click Security
  - On the bottom of the page, in the Less secure app access panel,
    click Turn on access
  - Click Save button

5.5 - Config Pialert parameters
  ```
  sed -i "s,'/home/pi/pialert','$HOME/pialert'," ~/pialert/config/pialert.conf          
  nano  ~/pialert/config/pialert.conf
  ```
  - If you want to use email reporting, configure this parameters
    ```ini
    REPORT_MAIL     = True
    REPORT_TO       = 'user@gmail.com'
    SMTP_SERVER     = 'smtp.gmail.com'
    SMTP_PORT       = 587
    SMTP_USER       = 'user@gmail.com'
    SMTP_PASS       = 'password'
    ```

  - If you want to update your Dynamic DNS, configure this parameters
    ```ini
    DDNS_ACTIVE     = True
    DDNS_DOMAIN     = 'your_domain.freeddns.org'
    DDNS_USER       = 'dynu_user'
    DDNS_PASSWORD   = 'A0000000B0000000C0000000D0000000'
    DDNS_UPDATE_URL = 'https://api.dynu.com/nic/update?'
    ```

  - If you have installed Pi.hole and DHCP, activate this parameters
    ```ini
    PIHOLE_ACTIVE   = True
    DHCP_ACTIVE     = True
    ```

5.6 - Update vendors DB
  ```
  python ~/pialert/back/pialert.py update_vendors
  ```
  or
  ```
  python3 ~/pialert/back/pialert.py update_vendors
  ```

5.7 - Test Pi.Alert Scan
  ```
  python ~/pialert/back/pialert.py internet_IP
  python ~/pialert/back/pialert.py 1
  ```
  or
  ```
  python3 ~/pialert/back/pialert.py internet_IP
  python3 ~/pialert/back/pialert.py 1
  ```

5.8 - Update crontab template with python3

  If you prefer to use Python 3 (installed in the previous block), you must
  update `pialert.cron` file with the correct command: `python3` instead of
  `python`
  ```
  sed -i 's/python/python3/g' ~/pialert/install/pialert.cron
  ```

5.9 - Add crontab jobs
  ```
  (crontab -l 2>/dev/null; cat ~/pialert/install/pialert.cron) | crontab -
  ```

5.10 - Add permissions to the web-server user
  ```
  sudo chgrp -R www-data ~/pialert/db
  chmod -R 770 ~/pialert/db
  ```

5.11 - Check DNS record for pi.alert (explained in point 2.7 of Pi.hole
  installation)
  - Add pi.alert DNS Record
    ```
    hostname -I
    ```
    or this one if have severals interfaces
    ```
    ip -o route get 1 | sed 's/^.*src \([^ ]*\).*$/\1/;q'
    ```
    - Pi-hole admin portal -> Local DNS -> DNS Records -> Add new domain /IP
      - pi.alert    192.168.1.x
      - (*replace 192.168.1.x with your Raspberry IP*)

5.12 - Use admin panel to configure the devices
  - http://pi.alert/
  - http://192.168.1.x/pialert/
    - (*replace 192.168.1.x with your Raspberry IP*)


### Device Management
<!--- --------------------------------------------------------------------- --->

  - [Device Management instructions](./DEVICE_MANAGEMENT.md)

### License
  GPL 3.0
  [Read more here](../LICENSE.txt)

### Contact
  pi.alert.application@gmail.com
