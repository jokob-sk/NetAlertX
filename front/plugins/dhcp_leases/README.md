## Overview

A plugin allowing for importing devices from DHCP.leases files.  

### Usage

- Specify full paths of all `dhcp.leases` files you want to import and watch in the `DHCPLSS_paths_to_check`setting.
- Map the paths specified in the `DHCPLSS_paths_to_check`setting in your `docker-compose.yml` file.
- If you are using pihole or dnsmasq dhcp.leases, include `pihole` or `dnsmasq` into the mapping path respectively, check the below example for details


#### Example: 


`docker-compose.yml` excerpt:

```yaml
    volumes:
      ...
      # mapping different dhcp.leases files
      - /first/location/dhcp.leases:/mnt/dhcp1.leases
      - /second/location/dhcp.leases:/mnt/dhcp2.leases      
      - /third/location/dhcp.leases:/etc/pihole/dhcp.leases      # a pihole specific dhcp.leases file 
      - /fourth/location/dhcp.leases:/etc/dnsmasq/dhcp.leases    # a dnsmasq specific dhcp.leases file  
      ...
```

The `DHCPLSS_paths_to_check` setting should then contain the following: 

```python
DHCPLSS_paths_to_check = ['/mnt/dhcp1.leases','/mnt/dhcp2.leases','/etc/pihole/dhcp.leases','/etc/dnsmasq/dhcp.leases']
```

### Notes

No specific configuration is needed. This plugin supports `dhcp.leases` file(s) in the following formats:

1. PiHole
2. Dnsmasq
3. Generic format 

#### pihole format

Example File Format:  _(not all lines are required)_

```
TBC
```

#### dnsmasq format 

`[Lease expiry time] [mac address] [ip address] [hostname] [client id, if known]`

Example File Format:  _(not all lines are required)_

```
1715932537 01:5c:5c:5c:5c:5c:5c 192.168.1.115 ryans-laptop 01:5c:5c:5c:5c:5c:5c
```

> Note, only `[mac address] [ip address] [hostname]` are captured

#### Generic format  

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