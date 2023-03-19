## Overview

A plugin allowing for importing devices from DHCP.leases files.  

### Usage

- Specify full paths of all `dhcp.leases` files you want to import and watch in the `DHCPLSS_paths_to_check`setting.
- Map the paths specified in the `DHCPLSS_paths_to_check`setting in your `docker-compose.yml` file.

#### Example: 


`docker-compose.yml` excerpt:

```yaml
    volumes:
      ...
      # mapping different dhcp.leases files
      - /first/location/dhcp.leases:/mnt/dhcp1.leases
      - /second/location/dhcp.leases:/mnt/dhcp2.leases      
      ...
```

`DHCPLSS_paths_to_check` Setting: 

```python
DHCPLSS_paths_to_check = ['/mnt/dhcp1.leases','/mnt/dhcp2.leases']
```

### Notes

- No specific configuration needed.