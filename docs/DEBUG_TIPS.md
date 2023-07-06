## More Logging

When debugging an issue always set the highest log level:

`LOG_LEVEL='debug'`


## Check the _dev image and open issues

If possible, check if your issue got fixed in the `_dev` image before opening a new issue. The container is:

`jokobsk/pi.alert_dev:latest`

> ⚠ Please backup your DB and config beforehand!

PLease also search [open issues](https://github.com/jokob-sk/Pi.Alert/issues).

## Surfacing errors when container restarts

Start the container via the terminal with a command similar to this one:

```bash
docker run --rm --network=host \
  -v local/path/pialert/config:/home/pi/pialert/config \
  -v local/path/pialert/db:/home/pi/pialert/db \
  -e TZ=Europe/Berlin \
  -e PORT=20211 \
  jokobsk/pi.alert:latest

```

> ⚠ Please note, don't use the `-d` parameter so you see the error when the container crashes. Use this error in your issue description.

## Disable restart behavior

To prevent a Docker container from automatically restarting in a Docker Compose file, specify the restart policy as `no`:

```yaml
version: '3'

services:
  your-service:
    image: your-image:tag
    restart: no
    # Other service configurations...
```

