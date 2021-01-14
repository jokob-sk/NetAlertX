#
PIALERT_VERSION=2.55
PIALERT_DEV_PATH=/media/WD_4TB/dev

cd $PIALERT_DEV_PATH

tar tvf pialert/install/pialert_latest.tar | wc -l
rm pialert/install/pialert_*.tar

tar cvf pialert/install/pialert_$PIALERT_VERSION.tar --exclude="pialert/install" --exclude="pialert/.git" pialert | wc -l

# rm pialert/install/pialert_latest.tar
ln -s pialert_$PIALERT_VERSION.tar pialert/install/pialert_latest.tar



