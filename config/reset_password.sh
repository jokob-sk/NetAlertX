#!/bin/sh
PIA_CONF_FILE='pialert.conf'
PIA_PASS=$1
echo "Check of key PIALERT_WEB_PROTECTION exists:"
CHECK_PROT=$(grep "PIALERT_WEB_PROTECTION" $PIA_CONF_FILE | wc -l)
if [ $CHECK_PROT -eq 0 ]
then
    cp $PIA_CONF_FILE $PIA_CONF_FILE.bak1
    echo "   Key not found. Key 'PIALERT_WEB_PROTECTION' will be created."
    echo "   Check Config after the script is finished."
    sed -i "/^VENDORS_DB.*/a PIALERT_WEB_PROTECTION = False" $PIA_CONF_FILE > pialert.tmp
else
    echo "   Key exists. Nothing to do."
fi
echo ""
echo "Check of key PIALERT_WEB_PASSWORD exists:"
CHECK_PWD=$(grep "PIALERT_WEB_PASSWORD" $PIA_CONF_FILE | wc -l)
if [ $CHECK_PWD -eq 0 ]
then
    cp $PIA_CONF_FILE $PIA_CONF_FILE.bak2
    echo "   Key not found. Key 'PIALERT_WEB_PASSWORD' will be created."
    echo "   Check Config after the script is finished."
    echo "   If the key is just created, please run the script again to set a new password".
    sed -i "/^PIALERT_WEB_PROTECTION.*/a PIALERT_WEB_PASSWORD = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'" $PIA_CONF_FILE
else
    echo "   The password '$1' is hashed"
    PIA_PASS_HASH=$(echo -n $PIA_PASS | sha256sum | awk '{print $1}')
    echo "   The hashed password is:"
    echo "   $PIA_PASS_HASH"
    sed -i "/PIALERT_WEB_PASSWORD/c\PIALERT_WEB_PASSWORD = '$PIA_PASS_HASH'" $PIA_CONF_FILE
    echo "   The hash was saved in the configuration file"
fi
