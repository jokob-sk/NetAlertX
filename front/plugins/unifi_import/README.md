## Overview

A plugin allowing for importing devices from a UniFi controller. The plugin also tries to import the network map. 

### Usage

Specify the following settings in the Settings section of NetAlertX:

- `UNFIMP_username` - Username used to log in the UNIFI controller.
- `UNFIMP_password` - Password used to log in the UNIFI controller.
- `UNFIMP_host` - Host URL or IP address where the UNIFI controller is hosted (excluding `http://`)
- `UNFIMP_sites` - Name of the sites (usually 'default', check the URL in your UniFi controller UI if unsure. The site id is in the following part of the URL: `https://192.168.1.1:8443/manage/site/this-is-the-site-id/settings/`). 
- `UNFIMP_protocol` - https:// or http://
- `UNFIMP_port` - Usually `8443` or `8843` 
- `UNFIMP_version` - e.g. `UDMP-unifiOS` is used for the "Cloud Gateway Ultra"


### Notes

- It is recommended to create a read-only user in your UniFi controller 