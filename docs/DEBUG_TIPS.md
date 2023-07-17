# Debugging and troubleshooting

Please follow tips 1 - 4 to get a more detailed error. 

## 1. More Logging 📃

When debugging an issue always set the highest log level:

`LOG_LEVEL='debug'`


## 2. Surfacing errors when container restarts 🔁

Start the container via the **terminal** with a command similar to this one:

```bash
docker run --rm --network=host \
  -v local/path/pialert/config:/home/pi/pialert/config \
  -v local/path/pialert/db:/home/pi/pialert/db \
  -e TZ=Europe/Berlin \
  -e PORT=20211 \
  jokobsk/pi.alert:latest

```

> ⚠ Please note, don't use the `-d` parameter so you see the error when the container crashes. Use this error in your issue description.

## 3. Check the _dev image and open issues ❓

If possible, check if your issue got fixed in the `_dev` image before opening a new issue. The container is:

`jokobsk/pi.alert_dev:latest`

> ⚠ Please backup your DB and config beforehand!

Please also search [open issues](https://github.com/jokob-sk/Pi.Alert/issues).

## 4. Disable restart behavior 🛑

To prevent a Docker container from automatically restarting in a Docker Compose file, specify the restart policy as `no`:

```yaml
version: '3'

services:
  your-service:
    image: your-image:tag
    restart: no
    # Other service configurations...
```

## 📃Common issues

### Permissions

* If facing issues (AJAX errors, can't write to DB, empty screen, etc,) make sure permissions are set correctly, and check the logs under `/home/pi/pialert/front/log`. 
* To solve permission issues you can try setting the owner and group of the `pialert.db` by executing the following on the host system: `docker exec pialert chown -R www-data:www-data /home/pi/pialert/db/pialert.db`. 
* Map to local User and Group IDs. Specify the enviroment variables `HOST_USER_ID` and `HOST_USER_GID` if needed.
* If still facing issues, try to map the pialert.db file (⚠ not folder) to `:/home/pi/pialert/db/pialert.db` (see Examples below for details)

### Container restarts / crashes

* Check the logs for details. Often a required setting for a notification method is missing. 

### unable to resolve host

* Check that your `SCAN_SUBNETS` variable is using the correct mask and `--interface` as outlined in the instructions above. 

### Invalid JSON

Check the [Invalid JSON errors debug help](/docs/DEBUG_INVALID_JSON.md) docs on how to proceed.

### sudo execution failing (e.g.: on arpscan) on a Raspberry Pi 4 

> sudo: unexpected child termination condition: 0

Resolution based on [this issue](https://github.com/linuxserver/docker-papermerge/issues/4#issuecomment-1003657581)

```
wget ftp.us.debian.org/debian/pool/main/libs/libseccomp/libseccomp2_2.5.3-2_armhf.deb
sudo dpkg -i libseccomp2_2.5.3-2_armhf.deb
```

The link above will probably break in time too. Go to https://packages.debian.org/sid/armhf/libseccomp2/download to find the new version number and put that in the url.
