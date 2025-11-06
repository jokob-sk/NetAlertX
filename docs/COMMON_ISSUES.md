### Loading...

Often if the application is misconfigured the `Loading...` dialog is continuously displayed. This is most likely caused by the backed failing to start. The **Maintenance -> Logs** section should give you more details on what's happening. If there is no exception, check the Portainer log, or start the container in the foreground (without the `-d` parameter) to observe any exceptions. It's advisable to enable `trace` or `debug`. Check the [Debug tips](./DEBUG_TIPS.md) on detailed instructions. 

### Incorrect SCAN_SUBNETS

One of the most common issues is not configuring `SCAN_SUBNETS` correctly. If this setting is misconfigured you will only see one or two devices in your devices list after a scan. Please read the [subnets docs](./SUBNETS.md) carefully to resolve this.

### Duplicate devices and notifications

The app uses the MAC address as an unique identifier for devices. If a new MAC is detected a new device is added to the application and corresponding notifications are triggered. This means that if the MAC of an existing device changes, the device will be logged as a new device. You can usually prevent this from happening by changing the device configuration (in Android, iOS, or Windows) for your network. See the [Random Macs](./RANDOM_MAC.md) guide for details. 

### Permissions

Make sure you [File permissions](./FILE_PERMISSIONS.md) are set correctly.

* If facing issues (AJAX errors, can't write to DB, empty screen, etc,) make sure permissions are set correctly, and check the logs under `/app/log`. 
* To solve permission issues you can try setting the owner and group of the `app.db` by executing the following on the host system: `docker exec netalertx chown -R www-data:www-data /app/db/app.db`. 
* If still facing issues, try to map the app.db file (⚠ not folder) to `:/app/db/app.db` (see [docker-compose Examples](./DOCKER_COMPOSE.md) for details)

### Container restarts / crashes

* Check the logs for details. Often a required setting for a notification method is missing. 

### unable to resolve host

* Check that your `SCAN_SUBNETS` variable is using the correct mask and `--interface`. See the [subnets docs for details](./SUBNETS.md).  

### Invalid JSON

Check the [Invalid JSON errors debug help](./DEBUG_INVALID_JSON.md) docs on how to proceed.

### sudo execution failing (e.g.: on arpscan) on a Raspberry Pi 4 

> sudo: unexpected child termination condition: 0

Resolution based on [this issue](https://github.com/linuxserver/docker-papermerge/issues/4#issuecomment-1003657581)

```
wget ftp.us.debian.org/debian/pool/main/libs/libseccomp/libseccomp2_2.5.3-2_armhf.deb
sudo dpkg -i libseccomp2_2.5.3-2_armhf.deb
```

The link above will probably break in time too. Go to https://packages.debian.org/sid/armhf/libseccomp2/download to find the new version number and put that in the url.

### Only Router and own device show up

Make sure that the subnet and interface in `SCAN_SUBNETS` are correct. If your device/NAS has multiple ethernet ports, you probably need to change `eth0` to something else.

### Losing my settings and devices after an update

If you lose your devices and/or settings after an update that means you don't have the `/app/db` and `/app/config` folders mapped to a permanent storage. That means every time you update these folders are re-created. Make sure you have the [volumes specified correctly](./DOCKER_COMPOSE.md) in your `docker-compose.yml` or run command.


### The application is slow

Slowness is usually caused by incorrect settings (the app might restart, so check the `app.log`), too many background processes (disable unnecessary scanners), too long scans (limit the number of scanned devices), too many disk operations, or some maintenance plugins might have failed. See the [Performance tips](./PERFORMANCE.md) docs for details.