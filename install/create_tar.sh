#
PIALERT_VERSION=`awk '$1=="VERSION" { print $3 }' ../back/pialert.conf | tr -d \'`
PIALERT_DEV_PATH=/media/WD_4TB/dev

cd $PIALERT_DEV_PATH
pwd

ls -l pialert/install/pialert*.tar
tar tvf pialert/install/pialert_latest.tar | wc -l
rm pialert/install/pialert_*.tar

tar cvf pialert/install/pialert_$PIALERT_VERSION.tar --exclude="pialert/install" --exclude="pialert/.git" pialert | wc -l

ln -s pialert_$PIALERT_VERSION.tar pialert/install/pialert_latest.tar
ls -l pialert/install/pialert*.tar



