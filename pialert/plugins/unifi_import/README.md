## Overview

A plugin allowing for importing devices from a UniFi controller.  

### Usage

Specify the following settings in the Settings section of PiAlert:

- `UNFIMP_username` - Username used to login into the UNIFI controller.
- `UNFIMP_password` - Password used to login into the UNIFI controller.
- `UNFIMP_host` - Host url or IP address where the UNIFI controller is hosted (excluding http://)
- `UNFIMP_sites` - Name of the sites (usually 'default', check the URL in your UniFi controller UI if unsure. The site id is in the following part of the URL: `https://192.168.1.1:8443/manage/site/this-is-the-site-id/settings/`). 
- `UNFIMP_protocol` - https:// or http://
- `UNFIMP_port` - Usually 8443

### Notes

- Currently only used to import devices, not their status, type or network map.
- It is recommend to create a read-only user in your UniFi controller 