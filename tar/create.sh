#!/bin/sh
# ------------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  create_tar.sh - Create the tar file for installation
# ------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
# ------------------------------------------------------------------------------

PIALERT_DEV_PATH=../../
cd $PIALERT_DEV_PATH
pwd
PIALERT_VERSION=`awk '$1=="VERSION" { print $3 }' pialert/config/version.conf | tr -d \'`

# ------------------------------------------------------------------------------
ls -l pialert/tar/pialert*.tar
tar tvf pialert/tar/pialert_latest.tar | wc -l
rm pialert/tar/pialert_*.tar

# ------------------------------------------------------------------------------
tar cvf pialert/tar/pialert_latest.tar --no-xattrs --exclude="pialert/tar" --exclude="pialert/.git" --exclude="pialert/.gitignore" pialert | wc -l

#ln -s pialert_$PIALERT_VERSION.tar pialert/package/pialert_latest.tar
#ls -l pialert/package/pialert*.tar
