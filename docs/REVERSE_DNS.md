## Setting up better name discovery with Reverse DNS

If you are running a DNS server, such as **AdGuard**, set up **Private reverse DNS servers** for a better name resolution on your network. Enabling this setting will enable NetAlertX to execute dig and nslookup commands to automatically resolve device names based on their IP addresses.

> [!TIP]  
> Before proceeding, ensure that [name resolution plugins](./NAME_RESOLUTION.md) are enabled.  
> You can customize how names are cleaned using the `NEWDEV_NAME_CLEANUP_REGEX` setting.  
> To auto-update Fully Qualified Domain Names (FQDN), enable the `REFRESH_FQDN` setting.


> Example 1: Reverse DNS `disabled`
> 
> ```
> jokob@Synology-NAS:/$ nslookup 192.168.1.58
> ** server can't find 58.1.168.192.in-addr.arpa: NXDOMAIN
> ```

> Example 2: Reverse DNS `enabled`
> 
> ```
> jokob@Synology-NAS:/$ nslookup 192.168.1.58
> 45.1.168.192.in-addr.arpa       name = jokob-NUC.localdomain.
> ```

### Enabling reverse DNS in AdGuard

1. Navigate to **Settings** ->  **DNS Settings**
2. Locate **Private reverse DNS servers**
3. Enter your router IP address, such as `192.168.1.1`
4. Make sure you have **Use private reverse DNS resolvers** ticked.
5. Click **Apply** to save your settings.


### Specifying the DNS in the container

You can specify the DNS server in the docker-compose to improve name resolution on your network. 

```yaml
services:
  netalertx:
    container_name: netalertx
    image: "ghcr.io/jokob-sk/netalertx:latest"
    restart: unless-stopped
    volumes:
      -  /home/netalertx/config:/data/config
      -  /home/netalertx/db:/data/db
      -  /home/netalertx/log:/tmp/log
    environment:
      - TZ=Europe/Berlin
      - PORT=20211
    network_mode: host
    dns:           # specifying the DNS servers used for the container
      - 10.8.0.1
      - 10.8.0.17
```

### Using a custom resolv.conf file

You can configure a custom **/etc/resolv.conf** file in **docker-compose.yml** and set the nameserver to your LAN DNS server (e.g.: Pi-Hole). See the relevant [resolv.conf man](https://www.man7.org/linux/man-pages/man5/resolv.conf.5.html) entry for details. 

#### docker-compose.yml:

```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    image: "ghcr.io/jokob-sk/netalertx:latest"
    restart: unless-stopped
    volumes:
      - ./config/app.conf:/data/config/app.conf
      - ./db:/data/db
      - ./log:/tmp/log
      - ./config/resolv.conf:/etc/resolv.conf                          # Mapping the /resolv.conf file for better name resolution
    environment:
      - TZ=Europe/Berlin
      - PORT=20211
    ports:
      - "20211:20211"
    network_mode: host
```

#### ./config/resolv.conf:

The most important below is the `nameserver` entry (you can add multiple):

```
nameserver 192.168.178.11
options edns0 trust-ad
search example.com
```