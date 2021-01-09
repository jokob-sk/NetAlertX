PIALERT_VERSION=2.50
PIALERT_DEV_PATH=/media/WD_4TB/dev

cd $PIALERT_DEV_PATH
rm pialert/install/pialert_$PIALERT_VERSION.tar
tar cvf pialert/install/pialert_$PIALERT_VERSION.tar --exclude="pialert/install" --exclude="pialert/.git" pialert

