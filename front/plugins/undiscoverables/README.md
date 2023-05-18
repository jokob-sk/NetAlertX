## Overview

A plugin allowing for importing Un-Discoverable devices from the settings page.


### Usage

- Go to settings and find Un-Discoverabe Devices in the list of plugins.
- Enable the plugin by changing the RUN parameter from disabled to `once` or `always_after_scan`.
- Add the name of your device to the list. (remove the sample entry first)
- SAVE
- wait for the next scan to finish

#### Example: 



### Known Limitations
 - Un-Discoverable Devices always show as offline. That is expected as they can not be discovered by Pi.Alert.
 - All IPs are set to 0.0.0.0 therefore the "Random MAC" icon might show up.
