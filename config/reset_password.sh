cp pialert.conf pialert.conf.bak
PIA_PASS=$1
echo "The password '$1' is hashed"
PIA_PASS_HASH=$(echo -n $PIA_PASS | sha256sum | awk '{print $1}')
echo "The hashed password is: $PIA_PASS_HASH"
sed -i "/PIALERT_WEB_PASSWORD/c\PIALERT_WEB_PASSWORD = '$PIA_PASS_HASH'" pialert.conf
echo "The hash was saved in the configuration file"