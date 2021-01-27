#!/bin/bash
# ------------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  pialert_update.sh - Update script
# ------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
INSTALL_DIR=~
PIALERT_HOME="$INSTALL_DIR/pialert"
LOG="pialert_update_`date +"%Y-%m-%d_%H-%M"`.log"
PYTHON_BIN=python


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
main() {
  print_superheader "Pi.Alert Update"
  log "`date`"
  log "Logfile: $LOG"
  log ""

  set -e

  check_pialert_home
  check_python_version

  create_backup
  move_files
  clean_files

  download_pialert
  update_config
  update_db

  test_pialert
  
  print_header "Update process finished"
  print_msg ""

  move_logfile
}

# ------------------------------------------------------------------------------
# Create backup
# ------------------------------------------------------------------------------
create_backup() {
  print_msg "- Deleting previous Pi.Alert backups..."
  rm "$INSTALL_DIR/"pialert_update_backup_*.tar  2>/dev/null || :
  
  print_msg "- Creating new Pi.Alert backup..."
  cd "$INSTALL_DIR"
  tar cvf "$INSTALL_DIR"/pialert_update_backup_`date +"%Y-%m-%d_%H-%M"`.tar  \
    pialert --checkpoint=100 --checkpoint-action="ttyout=."     2>&1 >> "$LOG"
  echo ""
}

# ------------------------------------------------------------------------------
# Move files to the new directory
# ------------------------------------------------------------------------------
move_files() {
  if [ -e "$PIALERT_HOME/back/pialert.conf" ] ; then
    print_msg "- Moving pialert.conf to the new directory..."
    mkdir -p "$PIALERT_HOME/config"
    mv "$PIALERT_HOME/back/pialert.conf" "$PIALERT_HOME/config"
  fi
}

# ------------------------------------------------------------------------------
# Move files to the new directory
# ------------------------------------------------------------------------------
clean_files() {
  print_msg "- Cleaning previous version..."
  rm -r "$PIALERT_HOME/back"    2>/dev/null || :
  rm -r "$PIALERT_HOME/doc"     2>/dev/null || :
  rm -r "$PIALERT_HOME/docs"    2>/dev/null || :
  rm -r "$PIALERT_HOME/front"   2>/dev/null || :
  rm -r "$PIALERT_HOME/install" 2>/dev/null || :
  rm -r "$PIALERT_HOME/"*.txt   2>/dev/null || :
  rm -r "$PIALERT_HOME/"*.md    2>/dev/null || :
}

# ------------------------------------------------------------------------------
# Download and uncompress Pi.Alert
# ------------------------------------------------------------------------------
download_pialert() {
  if [ -f "$INSTALL_DIR/pialert_latest.tar" ] ; then
    print_msg "- Deleting previous downloaded tar file"
    rm -r "$INSTALL_DIR/pialert_latest.tar"
  fi
  
  print_msg "- Downloading update file..."
  curl -Lo "$INSTALL_DIR/pialert_latest.tar" \
    https://github.com/pucherot/Pi.Alert/raw/main/tar/pialert_latest.tar
  echo ""

  print_msg "- Uncompressing tar file"
  tar xf "$INSTALL_DIR/pialert_latest.tar" -C "$INSTALL_DIR" \
    --exclude='pialert/config/pialert.conf' --exclude='pialert/db/pialert.db' \
    --exclude='pialert/log/*'  \
    --checkpoint=100 --checkpoint-action="ttyout=."               2>&1 >> "$LOG"
  echo ""

  print_msg "- Deleting downloaded tar file..."
  rm -r "$INSTALL_DIR/pialert_latest.tar"
}

# ------------------------------------------------------------------------------
#  Update conf file
# ------------------------------------------------------------------------------
update_config() {
  print_msg "- Config backup..."
  cp "$PIALERT_HOME/config/pialert.conf" \
     "$PIALERT_HOME/config/pialert.conf.back"                     2>&1 >> "$LOG"

  print_msg "- Updating config file..."
  sed -i '/VERSION/d' "$PIALERT_HOME/config/pialert.conf"         2>&1 >> "$LOG"
  sed -i 's/PA_FRONT_URL/REPORT_DEVICE_URL/g' \
    "$PIALERT_HOME/config/pialert.conf"                           2>&1 >> "$LOG"
  
  if ! grep -Fq PIALERT_PATH "$PIALERT_HOME/config/pialert.conf" ; then
    echo "PIALERT_PATH    = '$PIALERT_HOME'" >> \
         "$PIALERT_HOME/config/pialert.conf"
  fi      

  if ! grep -Fq QUERY_MYIP_SERVER "$PIALERT_HOME/config/pialert.conf" ; then
    echo "QUERY_MYIP_SERVER = 'http://ipv4.icanhazip.com'" >> \
         "$PIALERT_HOME/config/pialert.conf"
  fi      
}

# ------------------------------------------------------------------------------
# 
# ------------------------------------------------------------------------------
update_db() {
  print_msg "- Updating DB permissions..."
  sudo chgrp -R www-data $PIALERT_HOME/db                         2>&1 >> "$LOG"
  chmod -R 770 $PIALERT_HOME/db                                   2>&1 >> "$LOG"
}

# ------------------------------------------------------------------------------
# Test Pi.Alert
# ------------------------------------------------------------------------------
test_pialert() {
  print_msg "- Testing Pi.Alert HW vendors database update process..."
  print_msg "*** PLEASE WAIT A COUPLE OF MINUTES..."
  stdbuf -i0 -o0 -e0 \
    $PYTHON_BIN $PIALERT_HOME/back/pialert.py update_vendors_silent  2>&1 \
                                                                | tee -ai "$LOG"

  echo ""
  print_msg "- Testing Pi.Alert Internet IP Lookup..."
  stdbuf -i0 -o0 -e0 \
    $PYTHON_BIN $PIALERT_HOME/back/pialert.py internet_IP  2>&1 | tee -ai "$LOG"

  echo ""
  print_msg "- Testing Pi.Alert Network scan..."
  print_msg "*** PLEASE WAIT A COUPLE OF MINUTES..."
  stdbuf -i0 -o0 -e0 \
    $PYTHON_BIN $PIALERT_HOME/back/pialert.py 1            2>&1 | tee -ai "$LOG"
}

# ------------------------------------------------------------------------------
# Check Pi.Alert Installation Path
# ------------------------------------------------------------------------------
check_pialert_home() {
  if [ ! -e "$PIALERT_HOME" ] ; then
    process_error "Pi.Alert directory dosn't exists: $PIALERT_HOME"
  fi
}

# ------------------------------------------------------------------------------
# Check Python versions available
# ------------------------------------------------------------------------------
check_python_version() {
  print_msg "- Checking Python..."
  if [ -f /usr/bin/python ] ; then
    PYTHON_BIN="python"
  elif [ -f /usr/bin/python3 ] ; then
    PYTHON_BIN="python3"
  else
    process_error "Python NOT installed"
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
  log "**             ERROR UPDATING PI.ALERT                    **"
  log "************************************************************"
  log "************************************************************"
  log ""
  log "$1"
  log ""
  log "Use 'cat $LOG' to view update log"
  log ""

  exit 1
}

# ------------------------------------------------------------------------------
  main
  exit 0
