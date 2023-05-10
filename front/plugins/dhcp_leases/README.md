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

- This plugin expects the dhcp.leases file(s) to be in the format of **dhcpd.leases** that is different to the format that PiHole uses. 
[dhcpd.leases(5) - Linux man page]( https://linux.die.net/man/5/dhcpd.leases#:~:text=This%20database%20is%20a%20free,file%20is%20the%20current%20one.) 

Example File Format:  _(not all lines are required)_

```
lease 192.168.79.15 {
  starts 0 2016/08/21 13:25:45;
  ends 0 2016/08/21 19:25:45;
  cltt 0 2016/08/21 13:25:45;
  binding state active;
  next binding state free;
  rewind binding state free;
  hardware ethernet 8c:1a:bf:11:00:ea;
  uid "\001\214\032\277\021\000\352";
  option agent.circuit-id 0:17;
  option agent.remote-id c0:a8:9:5;
  client-hostname "android-8182e21c852776e7";
}  
```
