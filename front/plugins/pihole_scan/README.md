## Overview

A plugin allowing for importing Un-Discoverable devices from the settings page.
The main usecase is to add dumb network gear like unmanaged hubs and switches to the network view.
There might be other usecases, please let me know.

### Usage

- Go to settings and find Un-Discoverabe Devices in the list of plugins.
- Enable the plugin by changing the RUN parameter from disabled to `once` or `always_after_scan`.
- Add the name of your device to the list. (remove the sample entry first)
- SAVE
- wait for the next scan to finish

#### Examples:
Settings:
![settings](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/52883307-19a5-4602-b13a-9825461f6cc4)

resulting in these devices:
![devices](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/9f7659e7-75a8-4ae9-9f5f-781bdbcbc949)

Allowing Un-Discoverable devices like hubs, switches or APs to be added to the network view.
![network](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/b5ccc3b3-f5fd-4f5b-b0f0-e4e637c6da33)

### Known Limitations
 - Un-Discoverable Devices always show as offline. That is expected as they can not be discovered by Pi.Alert.
 - All IPs are set to 0.0.0.0 therefore the "Random MAC" icon might show up.
