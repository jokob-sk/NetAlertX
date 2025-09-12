# Reverse Proxy Configuration

> Submitted by amazing [cvc90](https://github.com/cvc90) 🙏

> [!NOTE] 
> There are various NGINX config files for NetAlertX, some for the bare-metal install, currently Debian 12 and Ubuntu 24 (`netalertx.conf`), and one for the docker container (`netalertx.template.conf`).
> 
> The first one you can find in the respective bare metal installer folder `/app/install/\<system\>/netalertx.conf`.
> The docker one can be found in the [install](https://github.com/jokob-sk/NetAlertX/tree/main/install) folder. Map, or use, the one appropriate for your setup.

<br/>

## NGINX HTTP Configuration (Direct Path)

1. On your NGINX server, create a new file called /etc/nginx/sites-available/netalertx

2. In this file, paste the following code:

```
   server { 
     listen 80; 
     server_name netalertx; 
     proxy_preserve_host on; 
     proxy_pass http://localhost:20211/; 
     proxy_pass_reverse http://localhost:20211/; 
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Check your config with `nginx -t`. If there are any issues, it will tell you.

5. Once NGINX restarts, you should be able to access the proxy website at http://netalertx/

<br/>

## NGINX HTTP Configuration (Sub Path)

1. On your NGINX server, create a new file called /etc/nginx/sites-available/netalertx

2. In this file, paste the following code:

```
   server { 
     listen 80; 
     server_name netalertx; 
     proxy_preserve_host on; 
     location ^~ /netalertx/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /netalertx/$1;
          rewrite ^/netalertx/?(.*)$ /$1 break;			
     }
    }
``` 

4. Check your config with `nginx -t`. If there are any issues, it will tell you.

5. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

6. Once NGINX restarts, you should be able to access the proxy website at http://netalertx/netalertx/

<br/>

## NGINX HTTP Configuration (Sub Path) with module ngx_http_sub_module

1. On your NGINX server, create a new file called /etc/nginx/sites-available/netalertx

2. In this file, paste the following code:

```
   server { 
     listen 80; 
     server_name netalertx; 
     proxy_preserve_host on; 
     location ^~ /netalertx/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /netalertx/$1;
          rewrite ^/netalertx/?(.*)$ /$1 break;
	  sub_filter_once off;
	  sub_filter_types *;
	  sub_filter 'href="/' 'href="/netalertx/';
	  sub_filter '(?>$host)/css' '/netalertx/css';
	  sub_filter '(?>$host)/js'  '/netalertx/js';
	  sub_filter '/img' '/netalertx/img';
	  sub_filter '/lib' '/netalertx/lib';
	  sub_filter '/php' '/netalertx/php';				
     }
    }
``` 

3. Check your config with `nginx -t`. If there are any issues, it will tell you.
   
4. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

5. Once NGINX restarts, you should be able to access the proxy website at http://netalertx/netalertx/

<br/>

**NGINX HTTPS Configuration (Direct Path)**

1. On your NGINX server, create a new file called /etc/nginx/sites-available/netalertx

2. In this file, paste the following code:

```
   server { 
     listen 443; 
     server_name netalertx; 
     SSLEngine On;
     SSLCertificateFile /etc/ssl/certs/netalertx.pem;
     SSLCertificateKeyFile /etc/ssl/private/netalertx.key;
     proxy_preserve_host on; 
     proxy_pass http://localhost:20211/; 
     proxy_pass_reverse http://localhost:20211/; 
    }
``` 

4. Check your config with `nginx -t`. If there are any issues, it will tell you.

5. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

6. Once NGINX restarts, you should be able to access the proxy website at https://netalertx/

<br/>

**NGINX HTTPS Configuration (Sub Path)**

1. On your NGINX server, create a new file called /etc/nginx/sites-available/netalertx

2. In this file, paste the following code:

```
   server { 
     listen 443; 
     server_name netalertx; 
     SSLEngine On;
     SSLCertificateFile /etc/ssl/certs/netalertx.pem;
     SSLCertificateKeyFile /etc/ssl/private/netalertx.key;
     location ^~ /netalertx/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /netalertx/$1;
          rewrite ^/netalertx/?(.*)$ /$1 break;		
     }
    }
``` 

4. Check your config with `nginx -t`. If there are any issues, it will tell you.
   
5. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

6. Once NGINX restarts, you should be able to access the proxy website at https://netalertx/netalertx/

<br/>

## NGINX HTTPS Configuration (Sub Path) with module ngx_http_sub_module

1. On your NGINX server, create a new file called /etc/nginx/sites-available/netalertx

2. In this file, paste the following code:

```
   server { 
     listen 443; 
     server_name netalertx; 
     SSLEngine On;
     SSLCertificateFile /etc/ssl/certs/netalertx.pem;
     SSLCertificateKeyFile /etc/ssl/private/netalertx.key;
     location ^~ /netalertx/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /netalertx/$1;
          rewrite ^/netalertx/?(.*)$ /$1 break;
	  sub_filter_once off;
	  sub_filter_types *;
	  sub_filter 'href="/' 'href="/netalertx/';
	  sub_filter '(?>$host)/css' '/netalertx/css';
	  sub_filter '(?>$host)/js'  '/netalertx/js';
	  sub_filter '/img' '/netalertx/img';
	  sub_filter '/lib' '/netalertx/lib';
	  sub_filter '/php' '/netalertx/php';		
     }
    }
``` 

4. Check your config with `nginx -t`. If there are any issues, it will tell you.
   
5. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

6. Once NGINX restarts, you should be able to access the proxy website at https://netalertx/netalertx/

<br/>

## Apache HTTP Configuration (Direct Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/netalertx.conf.

2. In this file, paste the following code:

```
    <VirtualHost *:80>
         ServerName netalertx
         ProxyPreserveHost On
         ProxyPass / http://localhost:20211/
         ProxyPassReverse / http://localhost:20211/
    </VirtualHost>
``` 

4. Check your config with `httpd -t` (or `apache2ctl -t` on Debian/Ubuntu). If there are any issues, it will tell you.
   
5. Activate the new website by running the following command:

   `a2ensite netalertx` or `service apache2 reload`

6. Once Apache restarts, you should be able to access the proxy website at http://netalertx/

<br/>

## Apache HTTP Configuration (Sub Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/netalertx.conf.

2. In this file, paste the following code:

```
    <VirtualHost *:80>
         ServerName netalertx
         location ^~ /netalertx/ {
               ProxyPreserveHost On
               ProxyPass / http://localhost:20211/
               ProxyPassReverse / http://localhost:20211/
         }
    </VirtualHost>
```   

4. Check your config with `httpd -t` (or `apache2ctl -t` on Debian/Ubuntu). If there are any issues, it will tell you.
   
5. Activate the new website by running the following command:

   `a2ensite netalertx` or `service apache2 reload`

6. Once Apache restarts, you should be able to access the proxy website at http://netalertx/

<br/>

## Apache HTTPS Configuration (Direct Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/netalertx.conf.

2. In this file, paste the following code:

```
    <VirtualHost *:443>
         ServerName netalertx
         SSLEngine On
         SSLCertificateFile /etc/ssl/certs/netalertx.pem
         SSLCertificateKeyFile /etc/ssl/private/netalertx.key
         ProxyPreserveHost On
         ProxyPass / http://localhost:20211/
         ProxyPassReverse / http://localhost:20211/
    </VirtualHost>
```   

4. Check your config with `httpd -t` (or `apache2ctl -t` on Debian/Ubuntu). If there are any issues, it will tell you.
   
5. Activate the new website by running the following command:

    `a2ensite netalertx` or `service apache2 reload`

6. Once Apache restarts, you should be able to access the proxy website at https://netalertx/

<br/>

## Apache HTTPS Configuration (Sub Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/netalertx.conf.

2. In this file, paste the following code:
                            
```
	<VirtualHost *:443> 
        ServerName netalertx
        SSLEngine On 
        SSLCertificateFile /etc/ssl/certs/netalertx.pem
        SSLCertificateKeyFile /etc/ssl/private/netalertx.key
        location ^~ /netalertx/ {
              ProxyPreserveHost On
              ProxyPass / http://localhost:20211/
              ProxyPassReverse / http://localhost:20211/
        }
    </VirtualHost>
```       

4. Check your config with `httpd -t` (or `apache2ctl -t` on Debian/Ubuntu). If there are any issues, it will tell you.
   
5. Activate the new website by running the following command:

   `a2ensite netalertx` or `service apache2 reload`

6. Once Apache restarts, you should be able to access the proxy website at https://netalertx/netalertx/

<br/>

## Reverse proxy example by using LinuxServer's SWAG container.

> Submitted by [s33d1ing](https://github.com/s33d1ing). 🙏

## [linuxserver/swag](https://github.com/linuxserver/docker-swag)

In the SWAG container create `/config/nginx/proxy-confs/netalertx.subfolder.conf` with the following contents:

``` nginx
## Version 2023/02/05
# make sure that your netalertx container is named netalertx
# netalertx does not require a base url setting

# Since NetAlertX uses a Host network, you may need to use the IP address of the system running NetAlertX for $upstream_app.

location /netalertx {
    return 301 $scheme://$host/netalertx/;
}

location ^~ /netalertx/ {
    # enable the next two lines for http auth
    #auth_basic "Restricted";
    #auth_basic_user_file /config/nginx/.htpasswd;

    # enable for ldap auth (requires ldap-server.conf in the server block)
    #include /config/nginx/ldap-location.conf;

    # enable for Authelia (requires authelia-server.conf in the server block)
    #include /config/nginx/authelia-location.conf;

    # enable for Authentik (requires authentik-server.conf in the server block)
    #include /config/nginx/authentik-location.conf;

    include /config/nginx/proxy.conf;
    include /config/nginx/resolver.conf;

    set $upstream_app netalertx;
    set $upstream_port 20211;
    set $upstream_proto http;

    proxy_pass $upstream_proto://$upstream_app:$upstream_port;
    proxy_set_header Accept-Encoding "";

    proxy_redirect ~^/(.*)$ /netalertx/$1;
    rewrite ^/netalertx/?(.*)$ /$1 break;

    sub_filter_once off;
    sub_filter_types *;

    sub_filter 'href="/' 'href="/netalertx/';

    sub_filter '(?>$host)/css' '/netalertx/css';
    sub_filter '(?>$host)/js'  '/netalertx/js';

    sub_filter '/img' '/netalertx/img';
    sub_filter '/lib' '/netalertx/lib';
    sub_filter '/php' '/netalertx/php';
}
```

<br/>

## Traefik

> Submitted by [Isegrimm](https://github.com/Isegrimm) 🙏 (based on this [discussion](https://github.com/jokob-sk/NetAlertX/discussions/449#discussioncomment-7281442))

Assuming the user already has a working Traefik setup, this is what's needed to make NetAlertX work at a URL like www.domain.com/netalertx/. 

Note: Everything in these configs assumes '**www.domain.com**' as your domainname and '**section31**' as an arbitrary name for your certificate setup. You will have to substitute these with your own.

Also, I use the prefix '**netalertx**'. If you want to use another prefix, change it in these files: dynamic.toml and default.

Content of my yaml-file (this is the generic Traefik config, which defines which ports to listen on, redirect http to https and sets up the certificate process).
It also contains Authelia, which I use for authentication.
This part contains nothing specific to NetAlertX.

```yaml
version: '3.8'

services:
  traefik:
    image: traefik
    container_name: traefik
    command:
      - "--api=true"
      - "--api.insecure=true"
      - "--api.dashboard=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--providers.file.filename=/traefik-config/dynamic.toml"
      - "--providers.file.watch=true"
      - "--log.level=ERROR"
      - "--certificatesresolvers.section31.acme.email=postmaster@domain.com"
      - "--certificatesresolvers.section31.acme.storage=/traefik-config/acme.json"
      - "--certificatesresolvers.section31.acme.httpchallenge=true"
      - "--certificatesresolvers.section31.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - /appl/docker/traefik/config:/traefik-config
    depends_on:
      - authelia
    restart: unless-stopped
  authelia:
    container_name: authelia
    image: authelia/authelia:latest
    ports:
      - "9091:9091"
    volumes:
      - /appl/docker/authelia:/config
    restart: u
    nless-stopped
```
Snippet of the dynamic.toml file (referenced in the yml-file above) that defines the config for NetAlertX:
The following are self-defined keywords, everything else is traefik keywords:
- netalertx-router
- netalertx-service
- auth
- netalertx-stripprefix


```toml
[http.routers]
  [http.routers.netalertx-router]
    entryPoints = ["websecure"]
    rule = "Host(`www.domain.com`) && PathPrefix(`/netalertx`)"
    service = "netalertx-service"
    middlewares = "auth,netalertx-stripprefix"
    [http.routers.netalertx-router.tls]
       certResolver = "section31"
       [[http.routers.netalertx-router.tls.domains]]
         main = "www.domain.com"

[http.services]
  [http.services.netalertx-service]
    [[http.services.netalertx-service.loadBalancer.servers]]
      url = "http://internal-ip-address:20211/"

[http.middlewares]
  [http.middlewares.auth.forwardAuth]
    address = "http://authelia:9091/api/verify?rd=https://www.domain.com/authelia/"
    trustForwardHeader = true
    authResponseHeaders = ["Remote-User", "Remote-Groups", "Remote-Name", "Remote-Email"]
  [http.middlewares.netalertx-stripprefix.stripprefix]
    prefixes = "/netalertx"
    forceSlash = false

```
To make NetAlertX work with this setup I modified the default file at `/etc/nginx/sites-available/default` in the docker container by copying it to my local filesystem, adding the changes as specified by [cvc90](https://github.com/cvc90) and mounting the new file into the docker container, overwriting the original one. By mapping the file instead of changing the file in-place, the changes persist if an updated dockerimage is pulled. This is also a downside when the default file is updated, so I only use this as a temporary solution, until the dockerimage is updated with this change.

Default-file:

```
server {
    listen 80 default_server;
    root /var/www/html;
    index index.php;
    #rewrite /netalertx/(.*) / permanent;
    add_header X-Forwarded-Prefix "/netalertx" always;
    proxy_set_header X-Forwarded-Prefix "/netalertx";

  location ~* \.php$ {
    fastcgi_pass unix:/run/php/php8.2-fpm.sock;
    include         fastcgi_params;
    fastcgi_param   SCRIPT_FILENAME    $document_root$fastcgi_script_name;
    fastcgi_param   SCRIPT_NAME        $fastcgi_script_name;
    fastcgi_connect_timeout 75;
          fastcgi_send_timeout 600;
          fastcgi_read_timeout 600;
  }
}
```

Mapping the updated file (on the local filesystem at `/appl/docker/netalertx/default`) into the docker container:


```bash
docker run -d --rm --network=host \
  --name=netalertx \
  -v /appl/docker/netalertx/config:/app/config \
  -v /appl/docker/netalertx/db:/app/db \
  -v /appl/docker/netalertx/default:/etc/nginx/sites-available/default \
  -e TZ=Europe/Amsterdam \
  -e PORT=20211 \
  ghcr.io/jokob-sk/netalertx:latest

```
