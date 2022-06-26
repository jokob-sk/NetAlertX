#!/bin/bash
# ------------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  pialert_install.sh - Installation script
# ------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
  COLS=70
  ROWS=12
  
  INSTALL_DIR=~
  PIALERT_HOME="$INSTALL_DIR/pialert"
  
  LIGHTTPD_CONF_DIR="/etc/lighttpd"
  WEBROOT="/var/www/html"
  PIALERT_DEFAULT_PAGE=false
  
  LOG="pialert_install_`date +"%Y-%m-%d_%H-%M"`.log"
  
  # MAIN_IP=`ip -o route get 1 | sed -n 's/.*src \([0-9.]\+\).*/\1/p'`
  MAIN_IP=`ip -o route get 1 | sed 's/^.*src \([^ ]*\).*$/\1/;q'`
  
  PIHOLE_INSTALL=false
  PIHOLE_ACTIVE=false
  DHCP_ACTIVATE=false
  DHCP_ACTIVE=false
  
  DHCP_RANGE_START="192.168.1.200"
  DHCP_RANGE_END="192.168.1.251"
  DHCP_ROUTER="192.168.1.1"
  DHCP_LEASE="1"
  DHCP_DOMAIN="local"
  
  USE_PYTHON_VERSION=0
  PYTHON_BIN=python

  FIRST_SCAN_KNOWN=true
  
  REPORT_MAIL=False
  REPORT_TO=user@gmail.com
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=user@gmail.com
  SMTP_PASS=password
  
  DDNS_ACTIVE=False
  DDNS_DOMAIN='your_domain.freeddns.org'
  DDNS_USER='dynu_user'
  DDNS_PASSWORD='A0000000B0000000C0000000D0000000'
  DDNS_UPDATE_URL='https://api.dynu.com/nic/update?'


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
main() {
  print_superheader "Pi.Alert Installation"
  log "`date`"
  log "Logfile: $LOG"

  check_pialert_home
  ask_config

  set -e

  install_pihole
  activate_DHCP
  add_pialert_DNS
  install_lighttpd
  install_arpscan
  install_python
  install_pialert

  print_header "Installation process finished"
  print_msg "Use: - http://pi.alert/"
  print_msg "     - http://$MAIN_IP/pialert/"
  print_msg "To access Pi.Alert web"
  print_msg ""

  move_logfile
}


# ------------------------------------------------------------------------------
# Ask config questions
# ------------------------------------------------------------------------------
ask_config() {
  # Ask installation
  ask_yesno "This script will install Pi.Alert in this system using this path:\n$PIALERT_HOME" \
            "Do you want to continue ?"
  if ! $ANSWER ; then
    exit 1
  fi

  # Ask Pi-hole Installation
  PIHOLE_ACTIVE=false
  if [ -e /usr/local/bin/pihole ] || [ -e /etc/pihole ]; then
    PIHOLE_ACTIVE=true
  fi

  PIHOLE_INSTALL=false
  if $PIHOLE_ACTIVE ; then
    msgbox "Pi-hole is already installed in this system." \
           "Perfect: Pi-hole Installation is not necessary"
  else
    ask_yesno "Pi-hole is not installed." \
              "Do you want to install Pi-hole before installing Pi.Alert ?" "YES"
    if $ANSWER ; then
      PIHOLE_INSTALL=true
      msgbox "In the installation wizard of Pi-hole, select this options" \
             "'Install web admin interface' & 'Install web server lighttpd'"
    fi
  fi

  # Ask DHCP Activation
  DHCP_ACTIVE=false
  DHCP_ACTIVATE=false
  if $PIHOLE_ACTIVE ; then
    DHCP_ACTIVE=`sudo grep DHCP_ACTIVE /etc/pihole/setupVars.conf | awk -F= '/./{print $2}'`
    if [ "$DHCP_ACTIVE" = "" ] ; then DHCP_ACTIVE=false; fi
 
    if ! $DHCP_ACTIVE ; then
      ask_yesno "Pi-hole DHCP server is not active." \
                "Do you want to activate Pi-hole DHCP server ?"
      if $ANSWER ; then
        DHCP_ACTIVATE=true
      fi
    fi

  elif $PIHOLE_INSTALL ; then
    ask_yesno "Pi-hole installation." \
              "Do you want to activate Pi-hole DHCP server ?"
    if $ANSWER ; then
      DHCP_ACTIVATE=true
    fi
  fi

  if $DHCP_ACTIVATE ; then
    msgbox "Default DHCP options will be used. Range=$DHCP_RANGE_START - $DHCP_RANGE_END / Router=$DHCP_ROUTER / Domain=$DHCP_DOMAIN / Leases=$DHCP_LEASE h." \
           "You can change this values in your Pi-hole Admin Portal"
    msgbox "Make sure your router's DHCP server is disabled" \
           "when using the Pi-hole DHCP server!"
  fi

  # Ask Pi.Alert deafault page
  PIALERT_DEFAULT_PAGE=false
  if ! $PIHOLE_ACTIVE && ! $PIHOLE_INSTALL; then
    ask_yesno "As Pi-hole is not going to be available in this system," \
              "Do you want to use Pi.Alert as default web server page ?" "YES"
    if $ANSWER ; then
      PIALERT_DEFAULT_PAGE=true
    fi
  fi
  
  # Ask Python version
  ask_option "What Python version do you want to use ?" \
              3 \
              0 " - Use Python already installed in the system (DEFAULT)" \
              2 " - Use Python 2" \
              3 " - Use Python 3"
  if [ "$ANSWER" = "" ] ; then
    USE_PYTHON_VERSION=0
  else
    USE_PYTHON_VERSION=$ANSWER
  fi

  # Ask first scan options
  ask_yesno "First Scan options" \
            "Do you want to mark the new devices as known devices during the first scan?" "YES"
  FIRST_SCAN_KNOWN=$ANSWER

  # Ask e-mail notification config
  MAIL_REPORT=false
  ask_yesno "Pi.Alert can notify you by e-mail when a network event occurs" \
            "Do you want to activate this feature ?"
  if $ANSWER ; then
    ask_yesno "e-mail notification needs a SMTP server (i.e. smtp.gmail.com)" \
              "Do you want to continue activating this feature ?"
    MAIL_REPORT=$ANSWER
  fi

  if $MAIL_REPORT ; then
    ask_input "" "Notify alert to this e-mail address:" "user@gmail.com"
    REPORT_TO=$ANSWER

    ask_input "" "SMTP server:" "smtp.gmail.com"
    SMTP_SERVER=$ANSWER

    ask_input "" "SMTP user:" "user@gmail.com"
    SMTP_USER=$ANSWER

    ask_input "" "SMTP password:" "password"
    SMTP_PASS=$ANSWER
  fi

  # Ask Dynamic DNS config
  DDNS_ACTIVE=false
  ask_yesno "Pi.Alert can update your Dynamic DNS IP (i.e with www.dynu.net)" \
            "Do you want to activate this feature ?"
  if $ANSWER ; then
    ask_yesno "Dynamics DNS updater needs a DNS with IP Update Protocol" \
              "(i.e with www.dynu.net). Do you want to continue ?"
    DDNS_ACTIVE=$ANSWER
  fi

  if $DDNS_ACTIVE ; then
    ask_input "" "Domain to update:" "your_domain.freeddns.org"
    DDNS_DOMAIN=$ANSWER

    ask_input "" "DDNS user:" "dynu_user"
    DDNS_USER=$ANSWER

    ask_input "" "DDNS password:" "A0000000B0000000C0000000D0000000"
    DDNS_PASSWORD=$ANSWER

    ask_input "" "URL to update DDNS IP:" "https://api.dynu.com/nic/update?"
    DDNS_UPDATE_URL=$ANSWER
  fi
  
  # Final config message
  msgbox "Configuration finished. To update the configuration, edit file:" \
         "$PIALERT_HOME/config/pialert.conf"

  msgbox "" "The installation will start now"
}


# ------------------------------------------------------------------------------
# Install Pi-hole
# ------------------------------------------------------------------------------
install_pihole() {
  print_header "Pi-hole"

  if ! $PIHOLE_INSTALL ; then
    return
  fi

  print_msg "- Checking if Pi-hole is installed..."
  if [ -e /usr/local/bin/pihole ] || [ -e /etc/pihole ]; then
    print_msg "  - Pi-hole already installed"
    print_msg "`pihole -v 2>&1`"
    print_msg ""

    PIHOLE_ACTIVE=true
    return
  fi

  print_msg "- Installing Pi-hole..."
  print_msg "  - Pi-hole has its own logfile"
  curl -sSL https://install.pi-hole.net | bash
  print_msg ""
  PIHOLE_ACTIVE=true
}


# ------------------------------------------------------------------------------
# Activate DHCP
# ------------------------------------------------------------------------------
activate_DHCP() {
  if ! $DHCP_ACTIVATE ; then
    return
  fi

  if ! $PIHOLE_ACTIVE ; then
    return
  fi

  print_msg "- Checking if DHCP is active..."
  if [ -e /etc/pihole ]; then
    DHCP_ACTIVE= `grep DHCP_ACTIVE /etc/pihole/setupVars.conf | awk -F= '/./{print $2}'`
  fi

  if $DHCP_ACTIVE ; then
    print_msg "  - DHCP already active"
  fi

  print_msg "- Activating DHCP..."
  sudo pihole -a enabledhcp "$DHCP_RANGE_START" "$DHCP_RANGE_END" "$DHCP_ROUTER" "$DHCP_LEASE" "$DHCP_DOMAIN"   2>&1 >> "$LOG"
  DHCP_ACTIVE=true
}


# ------------------------------------------------------------------------------
# Add Pi.Alert DNS
# ------------------------------------------------------------------------------
add_pialert_DNS() {
  if ! $PIHOLE_ACTIVE ; then
    return
  fi

  print_msg "- Checking if 'pi.alert' is configured in Local DNS..."
  if grep -Fq pi.alert /etc/pihole/custom.list; then
    print_msg "  - 'pi.alert' already in Local DNS..."
    return
  fi

  print_msg "- Adding 'pi.alert' to Local DNS..."
  sudo sh -c "echo $MAIN_IP pi.alert >> /etc/pihole/custom.list"  2>&1 >> "$LOG"
  sudo pihole restartdns                                          2>&1 >> "$LOG"
}


# ------------------------------------------------------------------------------
# Install Lighttpd & PHP
# ------------------------------------------------------------------------------
install_lighttpd() {
  print_header "Lighttpd & PHP"

  print_msg "- Installing apt-utils..."
  sudo apt-get install apt-utils -y                               2>&1 >> "$LOG"

  # print_msg "- Installing lighttpd..."
  # sudo apt-get install lighttpd -y                                2>&1 >> "$LOG"
  
  print_msg "- Installing PHP..."
  sudo apt-get install php php-cgi php-fpm php-sqlite3 -y         2>&1 >> "$LOG"

  # print_msg "- Activating PHP..."
  # ERRNO=0
  # sudo lighttpd-enable-mod fastcgi-php 2>&1                 >>"$LOG" || ERRNO=$? 
  # log_no_screen "-- Command error code: $ERRNO"
  # if [ "$ERRNO" = "1" ] ; then
  #   process_error "Error activating PHP"
  # fi
  
  # print_msg "- Restarting lighttpd..."
  # sudo service lighttpd restart                                   2>&1 >> "$LOG"
  # sudo /etc/init.d/lighttpd restart                             2>&1 >> "$LOG"

  print_msg "- Installing sqlite3..."
  sudo apt-get install sqlite3 -y                                 2>&1 >> "$LOG"
}


# ------------------------------------------------------------------------------
# Install arp-scan & dnsutils
# ------------------------------------------------------------------------------
install_arpscan() {
  print_header "arp-scan & dnsutils"

  print_msg "- Installing arp-scan..."
  sudo apt-get install arp-scan -y                                2>&1 >> "$LOG"

  print_msg "- Testing arp-scan..."
  sudo arp-scan -l | head -n -3 | tail +3                        | tee -a "$LOG"

  print_msg "- Installing dnsutils & net-tools..."
  sudo apt-get install dnsutils net-tools -y                      2>&1 >> "$LOG"
}
  

# ------------------------------------------------------------------------------
# Install Python
# ------------------------------------------------------------------------------
install_python() {
  print_header "Python"

  check_python_versions

  if [ $USE_PYTHON_VERSION -eq 0 ] ; then
    print_msg "- Using the available Python version installed"
    if $PYTHON3 ; then
      print_msg "  - Python 3 is available"
      USE_PYTHON_VERSION=3
    elif $PYTHON2 ; then
      print_msg "  - Python 2 is available"
      USE_PYTHON_VERSION=2
    else
      print_msg "  - Python is not available in this system"
      print_msg "    - Python 3 will be installed"
      USE_PYTHON_VERSION=3
    fi
    echo ""
  fi

  if [ $USE_PYTHON_VERSION -eq 2 ] ; then
    if $PYTHON2 ; then
      print_msg "- Using Python 2"
    else
      print_msg "- Installing Python 2..."
      sudo apt-get install python -y                              2>&1 >> "$LOG"
    fi
    PYTHON_BIN="python"
  elif [ $USE_PYTHON_VERSION -eq 3 ] ; then
    if $PYTHON3 ; then
      print_msg "- Using Python 3"
    else
      print_msg "- Installing Python 3..."
      sudo apt-get install python3 -y                             2>&1 >> "$LOG"
    fi
    PYTHON_BIN="python3"
  else
    process_error "Unknown Python version to use: $USE_PYTHON_VERSION"
  fi
}


# ------------------------------------------------------------------------------
# Check Python versions available
# ------------------------------------------------------------------------------
check_python_versions() {
  print_msg "- Checking Python 2..."
  if [ -f /usr/bin/python ] ; then
    print_msg "  - Python 2 is installed"
    print_msg "    - `python -V 2>&1`"
    PYTHON2=true
  else
    print_msg "  - Python 2 is NOT installed"
    PYTHON2=false
  fi
  echo ""

  print_msg "- Checking Python 3..."
  if [ -f /usr/bin/python3 ] ; then
    print_msg "  - Python 3 is installed"
    print_msg "    - `python3 -V 2>&1`"
    PYTHON3=true
  else
    print_msg "  - Python 3 is NOT installed"
    PYTHON3=false
  fi
  echo ""
}


# ------------------------------------------------------------------------------
# Install Pi.Alert
# ------------------------------------------------------------------------------
install_pialert() {
  print_header "Pi.Alert"

  download_pialert
  configure_pialert
  test_pialert
  add_jobs_to_crontab
  publish_pialert
  set_pialert_default_page
}


# ------------------------------------------------------------------------------
# Download and uncompress Pi.Alert
# ------------------------------------------------------------------------------
download_pialert() {
  if [ -f "$INSTALL_DIR/pialert_latest.tar" ] ; then
    print_msg "- Deleting previous downloaded tar file"
    rm -r "$INSTALL_DIR/pialert_latest.tar"
  fi
  
  print_msg "- Downloading installation tar file..."
  curl -Lo "$INSTALL_DIR/pialert_latest.tar" https://github.com/leiweibau/Pi.Alert/raw/main/tar/pialert_latest.tar
  echo ""

  print_msg "- Uncompressing tar file"
  tar xf "$INSTALL_DIR/pialert_latest.tar" -C "$INSTALL_DIR" --checkpoint=100 --checkpoint-action="ttyout=."  2>&1 >> "$LOG"
  echo ""

  print_msg "- Deleting downloaded tar file..."
  rm -r "$INSTALL_DIR/pialert_latest.tar"
}


# ------------------------------------------------------------------------------
# Configure Pi.Alert parameters
# ------------------------------------------------------------------------------
configure_pialert() {
  print_msg "- Settting Pi.Alert config file"

  set_pialert_parameter PIALERT_PATH    "'$PIALERT_HOME'"
  
  set_pialert_parameter REPORT_MAIL     "$REPORT_MAIL"
  set_pialert_parameter REPORT_TO       "'$REPORT_TO'"
  set_pialert_parameter SMTP_SERVER     "'$SMTP_SERVER'"
  set_pialert_parameter SMTP_PORT       "$SMTP_PORT"
  set_pialert_parameter SMTP_USER       "'$SMTP_USER'"
  set_pialert_parameter SMTP_PASS       "'$SMTP_PASS'"

  set_pialert_parameter DDNS_ACTIVE     "$DDNS_ACTIVE"
  set_pialert_parameter DDNS_DOMAIN     "'$DDNS_DOMAIN'"
  set_pialert_parameter DDNS_USER       "'$DDNS_USER'"
  set_pialert_parameter DDNS_PASSWORD   "'$DDNS_PASSWORD'"
  set_pialert_parameter DDNS_UPDATE_URL "'$DDNS_UPDATE_URL'"

  set_pialert_parameter PIHOLE_ACTIVE   "$PIHOLE_ACTIVE"
  set_pialert_parameter DHCP_ACTIVE     "$DHCP_ACTIVE"
}


# ------------------------------------------------------------------------------
# Set Pi.Alert parameter
# ------------------------------------------------------------------------------
set_pialert_parameter() {
  if [ "$2" = "false" ] ; then
    VALUE="False"
  elif [ "$2" = "true" ] ; then
    VALUE="True"
  else
    VALUE="$2"
  fi
  
  sed -i "/^$1.*=/s|=.*|= $VALUE|" $PIALERT_HOME/config/pialert.conf  2>&1 >> "$LOG"
}


# ------------------------------------------------------------------------------
# Test Pi.Alert
# ------------------------------------------------------------------------------
test_pialert() {
  print_msg "- Testing Pi.Alert HW vendors database update process..."
  print_msg "*** PLEASE WAIT A COUPLE OF MINUTES..."
  stdbuf -i0 -o0 -e0  $PYTHON_BIN $PIALERT_HOME/back/pialert.py update_vendors_silent            2>&1 | tee -ai "$LOG"

  echo ""
  print_msg "- Testing Pi.Alert Internet IP Lookup..."
  stdbuf -i0 -o0 -e0  $PYTHON_BIN $PIALERT_HOME/back/pialert.py internet_IP                      2>&1 | tee -ai "$LOG"

  echo ""
  print_msg "- Testing Pi.Alert Network scan..."
  print_msg "*** PLEASE WAIT A COUPLE OF MINUTES..."
  stdbuf -i0 -o0 -e0  $PYTHON_BIN $PIALERT_HOME/back/pialert.py 1                                2>&1 | tee -ai "$LOG"

  if $FIRST_SCAN_KNOWN ; then
    echo ""
    print_msg "- Set devices as Known devices..."
    sqlite3 $PIALERT_HOME/db/pialert.db "UPDATE Devices SET dev_NewDevice=0, dev_AlertEvents=0 WHERE dev_NewDevice=1" 2>&1 >> "$LOG"
  fi
}

# ------------------------------------------------------------------------------
# Add Pi.Alert jobs to crontab
# ------------------------------------------------------------------------------
add_jobs_to_crontab() {
  if crontab -l 2>/dev/null | grep -Fq pialert ; then
    print_msg "- Pi.Alert crontab jobs already exists. This is your crontab:"
    crontab -l | grep -F pialert                           2>&1 | tee -ai "$LOG"
    return    
  fi

  print_msg "- Adding jobs to the crontab..."
  if [ $USE_PYTHON_VERSION -eq 3 ] ; then
    sed -i "s/\<python\>/$PYTHON_BIN/g" $PIALERT_HOME/install/pialert.cron
  fi

  (crontab -l 2>/dev/null || : ; cat $PIALERT_HOME/install/pialert.cron) | crontab -
}

# ------------------------------------------------------------------------------
# Publish Pi.Alert web
# ------------------------------------------------------------------------------
publish_pialert() {
  if [ -e "$WEBROOT/pialert" ] || [ -L "$WEBROOT/pialert" ] ; then
    print_msg "- Deleting previous Pi.Alert site"
    sudo rm -r "$WEBROOT/pialert"                                 2>&1 >> "$LOG"
  fi

  print_msg "- Setting permissions..."
  sudo chgrp -R www-data $PIALERT_HOME/db                         2>&1 >> "$LOG"
  chmod -R g+rwx $PIALERT_HOME/db                                 2>&1 >> "$LOG"
  chmod go+x $INSTALL_DIR                                         2>&1 >> "$LOG"

  print_msg "- Publishing Pi.Alert web..."
  sudo ln -s "$PIALERT_HOME/front" "$WEBROOT/pialert"             2>&1 >> "$LOG"

  # print_msg "- Configuring http://pi.alert/ redirection..."
  # if [ -e "$LIGHTTPD_CONF_DIR/conf-available/pialert_front.conf" ] ; then
  #   sudo rm -r "$LIGHTTPD_CONF_DIR/conf-available/pialert_front.conf"  2>&1 >> "$LOG"
  # fi
  # sudo cp "$PIALERT_HOME/install/pialert_front.conf" "$LIGHTTPD_CONF_DIR/conf-available"  2>&1 >> "$LOG"

  # if [ -e "$LIGHTTPD_CONF_DIR/conf-enabled/pialert_front.conf" ] || \
  #    [ -L "$LIGHTTPD_CONF_DIR/conf-enabled/pialert_front.conf" ] ; then
  #   sudo rm -r "$LIGHTTPD_CONF_DIR/conf-enabled/pialert_front.conf" 2>&1 >> "$LOG"
  # fi

  # sudo ln -s ../conf-available/pialert_front.conf  "$LIGHTTPD_CONF_DIR/conf-enabled/pialert_front.conf"  2>&1 >> "$LOG"

  # print_msg "- Restarting lighttpd..."
  # sudo sudo service lighttpd restart                              2>&1 >> "$LOG"
  # sudo /etc/init.d/lighttpd restart                             2>&1 >> "$LOG"
}

# ------------------------------------------------------------------------------
# Set Pi.Alert the default web server page
# ------------------------------------------------------------------------------
set_pialert_default_page() {
  if ! $PIALERT_DEFAULT_PAGE ; then
    return
  fi
  
  print_msg "- Setting Pi.Alert as default web server page..."

  # if [ -e "$WEBROOT/index.lighttpd.html" ] ; then
  #   if [ -e "$WEBROOT/index.lighttpd.html.orig" ] ; then
  #     sudo rm "$WEBROOT/index.lighttpd.html"                      2>&1 >> "$LOG"
  #   else
  #     sudo mv "$WEBROOT/index.lighttpd.html"  "$WEBROOT/index.lighttpd.html.orig"  2>&1 >> "$LOG"
  #   fi
  # fi

  # if [ -e "$WEBROOT/index.html" ] || [ -L "$WEBROOT/index.html" ] ; then
  #   if [ -e "$WEBROOT/index.html.orig" ] ; then
  #     sudo rm "$WEBROOT/index.html"                               2>&1 >> "$LOG"
  #   else
  #     sudo mv "$WEBROOT/index.html" "$WEBROOT/index.html.orig"    2>&1 >> "$LOG"
  #   fi
  # fi

  # sudo cp "$PIALERT_HOME/install/index.html" "$WEBROOT/index.html" 2>&1 >>"$LOG"
}

# ------------------------------------------------------------------------------
# Check Pi.Alert Installation Path
# ------------------------------------------------------------------------------
check_pialert_home() {
  mkdir -p "$INSTALL_DIR"
  if [ ! -d "$INSTALL_DIR" ] ; then
    process_error "Installation path does not exists: $INSTALL_DIR"
  fi

  if [ -e "$PIALERT_HOME" ] || [ -L "$PIALERT_HOME" ] ; then
    process_error "Pi.Alert path already exists: $PIALERT_HOME"
  fi
}


# ------------------------------------------------------------------------------
# Move Logfile
# ------------------------------------------------------------------------------
move_logfile() {
  NEWLOG="$PIALERT_HOME/log/$LOG"

  mkdir -p "$PIALERT_HOME/log"
  mv $LOG $NEWLOG

  LOG="$NEWLOG"
  NEWLOG=""
}


# ------------------------------------------------------------------------------
# ASK
# ------------------------------------------------------------------------------
msgbox() {
  LINE1=$(printf "%*s" $(((${#1}+$COLS-5)/2)) "$1")
  LINE2=$(printf "%*s" $(((${#2}+$COLS-5)/2)) "$2")

  END_DIALOG=false
  while ! $END_DIALOG ; do
    whiptail --title "Pi.Alert Installation" --msgbox "$LINE1\\n\\n$LINE2" $ROWS $COLS
    BUTTON=$?
    ask_cancel
    ANSWER=true
  done
}

ask_yesno() {
  LINE1=$(printf "%*s" $(((${#1}+$COLS-5)/2)) "$1")
  LINE2=$(printf "%*s" $(((${#2}+$COLS-5)/2)) "$2")

  if [ "$3" = "YES" ]; then
    DEF_BUTTON=""
  else
    DEF_BUTTON="--defaultno"
  fi

  END_DIALOG=false
  while ! $END_DIALOG ; do
    whiptail --title "Pi.Alert Installation" --yesno $DEF_BUTTON "$LINE1\\n\\n$LINE2" $ROWS $COLS
    BUTTON=$?
    ask_cancel
  done

  if [ "$BUTTON" = "0" ] ; then
    ANSWER=true
  else
    ANSWER=false
  fi
}

ask_option() {
  MENU_ARGS=("$@")
  MENU_ARGS=("${MENU_ARGS[@]:1}")

  END_DIALOG=false
  while ! $END_DIALOG ; do
    ANSWER=$(whiptail --title "Pi.Alert Installation" --menu "$1" $ROWS $COLS "${MENU_ARGS[@]}"  3>&2 2>&1 1>&3 )
    BUTTON=$?
    ask_cancel CANCEL
  done
}

ask_input() {
  LINE1=$(printf "%*s" $(((${#1}+$COLS-5)/2)) "$1")
  LINE2=$(printf "%*s" $(((${#2}+$COLS-5)/2)) "$2")

  END_DIALOG=false
  while ! $END_DIALOG ; do
    ANSWER=$(whiptail --title "Pi.Alert Installation" --inputbox "$LINE1\\n\\n$LINE2" $ROWS $COLS "$3" 3>&2 2>&1 1>&3 )
    BUTTON=$?
    ask_cancel CANCEL

    if $END_DIALOG && [ "$ANSWER" = "" ] ; then
      msgbox "" "You must enter a value"
      END_DIALOG=false
    fi
  done
}

ask_cancel() {
  LINE0="Do you want to cancel the installation process"
  LINE0=$(printf "\n\n%*s" $(((${#LINE0}+$COLS-5)/2)) "$LINE0")

  if [ "$BUTTON" = "1" ] && [ "$1" = "CANCEL" ] ; then BUTTON="255"; fi

  if [ "$BUTTON" = "255" ] ; then
    whiptail --title "Pi.Alert Installation" --yesno --defaultno "$LINE0" $ROWS $COLS

    if [ "$?" = "0" ] ; then
      process_error "Installation Aborted by User"
    fi
  else
    END_DIALOG=true
  fi
}

# ------------------------------------------------------------------------------
# Log
# ------------------------------------------------------------------------------
log() {
  echo "$1" | tee -a "$LOG"
}

log_no_screen () {
  echo "$1" >> "$LOG"
}

log_only_screen () {
  echo "$1"
}

print_msg() {
  log_no_screen ""
  log "$1"
}

print_superheader() {
  log ""
  log "############################################################"
  log " $1"
  log "############################################################"  
}

print_header() {
  log ""
  log "------------------------------------------------------------"
  log " $1"
  log "------------------------------------------------------------"
}

process_error() {
  log ""
  log "************************************************************"
  log "************************************************************"
  log "**            ERROR INSTALLING PI.ALERT                   **"
  log "************************************************************"
  log "************************************************************"
  log ""
  log "$1"
  log ""
  log "Use 'cat $LOG' to view installation log"
  log ""

  # msgbox "****** ERROR INSTALLING Pi.ALERT ******" "$1"
  exit 1
}

# ------------------------------------------------------------------------------
  main
  exit 0
