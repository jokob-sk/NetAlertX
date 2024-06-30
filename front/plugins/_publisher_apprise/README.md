## Overview

[Apprise](https://hub.docker.com/r/caronc/apprise) is a notification gateway/publisher that allows you to push notifications to 80+ different services. 

## Notes

You need to bring your own separate Apprise instance to use this publisher gateway. I suggest this [Apprise image](https://hub.docker.com/r/caronc/apprise).

### Usage

- Go to settings and fill in relevant details.
- Use the Apprise container's URL in the `APPRISE_HOST` setting.

