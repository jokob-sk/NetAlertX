## Setting up better name discovery with Reverse DNS

If you are running a DNS server, such as **AdGuard**, set up **Private reverse DNS servers** for a better name resolution on your network. Enabling this setting will enable NetAlertX to execute dig and nslookup commands to automatically resolve device names based on their IP addresses.


> Example 1: Reverse DNS `disabled`
> 
> ```
> jokob@Synology-NAS:/$ nslookup 192.168.1.58
> ** server can't find 58.1.168.192.in-addr.arpa: NXDOMAIN
> 
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


### Using a custom resolv.conf file

You can configure a custom **/etc/resolv.conf** file in **docker-compose.yml** and set the nameserver to your LAN DNS server (e.g.: Pi-Hole). See the relevant [resolv.conf man](https://www.man7.org/linux/man-pages/man5/resolv.conf.5.html) entry for details. 

#### docker-compose.yml:

```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    image: "jokobsk/netalertx:latest"
    restart: unless-stopped
    volumes:
      - ./config/app.conf:/app/config/app.conf
      - ./db:/app/db
      - ./log:/app/front/log
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