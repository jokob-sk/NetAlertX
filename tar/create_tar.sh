#!/bin/sh
# ------------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  create_tar.sh - Create the tar file for installation
# ------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
# ------------------------------------------------------------------------------

PIALERT_DEV_PATH=$(pwd)
cd $PIALERT_DEV_PATH'/../'

PIALERT_VERSION=`awk '$1=="VERSION" { print $3 }' config/version.conf | tr -d \'`
echo $PIALERT_VERSION

# ------------------------------------------------------------------------------
ls -l tar/pialert*.tar
tar tvf tar/pialert_latest.tar | wc -l
rm tar/pialert_*.tar

# ------------------------------------------------------------------------------
tar cvf tar/pialert_$PIALERT_VERSION.tar --exclude="tar" --exclude=".git" --exclude=".gitignore" ./ | wc -l

#ln -s pialert_$PIALERT_VERSION.tar tar/pialert_latest.tar
cp tar/pialert_$PIALERT_VERSION.tar tar/pialert_latest.tar
#ls -l tar/pialert*.tar