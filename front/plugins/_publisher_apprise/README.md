## Overview

[Apprise](https://hub.docker.com/r/caronc/apprise) is a notification gateway/publisher that allows you to push notifications to 80+ different services. 

## Notes

You need to bring your own separate Apprise instance to use this publisher gateway. I suggest this [Apprise image](https://hub.docker.com/r/caronc/apprise).

### Usage

- Go to settings and fill in relevant details.
- Use the Apprise container's URL in the `APPRISE_HOST` setting.

## Examples

### Telegram

![Telegram config](apprise_telegram.png)

#### Troubleshooting

1. Replace `<bottoken>` and `<chatid>` with your values.

2. Test telegram notification in browser

```
https://api.telegram.org/bot<bottoken>/sendMessage?chat_id=<chatid>&text=%40%40TEXT%40%40
```
3. Test apprise notification in console (replace `192.168.1.2:9999`  with your apprise ip and port)

```
curl -X POST -d '{"urls":"tgram://<bottoken>/<chatid>","body":"test body from curl","title":"test title from curl"}' -H "Content-Type: application/json" "http://192.168.1.2:9999/notify/"
```

4. Test from the docker apprise container console
```
apprise -vv -t "Test Message from apprise console" -b "Test Message from apprise console" \
   tgram://<bottoken>/<chatid>/
```


