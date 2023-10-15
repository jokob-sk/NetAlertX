# Reverse Proxy Configuration

> Submitted by amazing [cvc90](https://github.com/cvc90) 🙏

## NGINX HTTP Configuration (Direct Path)

1. On your NGINX server, create a new file called /etc/nginx/sites-available/pialert

2. In this file, paste the following code:

```
   server { 
     listen 80; 
     server_name pi.alert; 
     proxy_preserve_host on; 
     proxy_pass http://localhost:20211/; 
     proxy_pass_reverse http://localhost:20211/; 
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Once NGINX restarts, you should be able to access the proxy website at http://pi.alert/

<br>

## NGINX HTTP Configuration (Sub Path)

1. On your NGINX server, create a new file called /etc/nginx/sites-available/pialert

2. In this file, paste the following code:

```
   server { 
     listen 80; 
     server_name pi.alert; 
     proxy_preserve_host on; 
     location ^~ /pi.alert/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /pi.alert/$1;
          rewrite ^/pi.alert/?(.*)$ /$1 break;			
     }
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Once NGINX restarts, you should be able to access the proxy website at http://pi.alert/pi.alert/

<br>

## NGINX HTTP Configuration (Sub Path) with module ngx_http_sub_module

1. On your NGINX server, create a new file called /etc/nginx/sites-available/pialert

2. In this file, paste the following code:

```
   server { 
     listen 80; 
     server_name pi.alert; 
     proxy_preserve_host on; 
     location ^~ /pi.alert/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /pi.alert/$1;
          rewrite ^/pi.alert/?(.*)$ /$1 break;
	  sub_filter_once off;
	  sub_filter_types *;
	  sub_filter 'href="/' 'href="/pi.alert/';
	  sub_filter '(?>$host)/css' '/pi.alert/css';
	  sub_filter '(?>$host)/js'  '/pi.alert/js';
	  sub_filter '/img' '/pi.alert/img';
	  sub_filter '/lib' '/pi.alert/lib';
	  sub_filter '/php' '/pi.alert/php';				
     }
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Once NGINX restarts, you should be able to access the proxy website at http://pi.alert/pi.alert/

<br>

**NGINX HTTPS Configuration (Direct Path)**

1. On your NGINX server, create a new file called /etc/nginx/sites-available/pialert

2. In this file, paste the following code:

```
   server { 
     listen 443; 
     server_name pi.alert; 
     SSLEngine On;
     SSLCertificateFile /etc/ssl/certs/pi.alert.pem;
     SSLCertificateKeyFile /etc/ssl/private/pi.alert.key;
     proxy_preserve_host on; 
     proxy_pass http://localhost:20211/; 
     proxy_pass_reverse http://localhost:20211/; 
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Once NGINX restarts, you should be able to access the proxy website at https://pi.alert/

<br>

**NGINX HTTPS Configuration (Sub Path)**

1. On your NGINX server, create a new file called /etc/nginx/sites-available/pialert

2. In this file, paste the following code:

```
   server { 
     listen 443; 
     server_name pi.alert; 
     SSLEngine On;
     SSLCertificateFile /etc/ssl/certs/pi.alert.pem;
     SSLCertificateKeyFile /etc/ssl/private/pi.alert.key;
     location ^~ /pi.alert/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /pi.alert/$1;
          rewrite ^/pi.alert/?(.*)$ /$1 break;		
     }
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Once NGINX restarts, you should be able to access the proxy website at https://pi.alert/pi.alert/

<br>

## NGINX HTTPS Configuration (Sub Path) with module ngx_http_sub_module

1. On your NGINX server, create a new file called /etc/nginx/sites-available/pialert

2. In this file, paste the following code:

```
   server { 
     listen 443; 
     server_name pi.alert; 
     SSLEngine On;
     SSLCertificateFile /etc/ssl/certs/pi.alert.pem;
     SSLCertificateKeyFile /etc/ssl/private/pi.alert.key;
     location ^~ /pi.alert/ {
          proxy_pass http://localhost:20211/;
          proxy_pass_reverse http://localhost:20211/; 
          proxy_redirect ~^/(.*)$ /pi.alert/$1;
          rewrite ^/pi.alert/?(.*)$ /$1 break;
	  sub_filter_once off;
	  sub_filter_types *;
	  sub_filter 'href="/' 'href="/pi.alert/';
	  sub_filter '(?>$host)/css' '/pi.alert/css';
	  sub_filter '(?>$host)/js'  '/pi.alert/js';
	  sub_filter '/img' '/pi.alert/img';
	  sub_filter '/lib' '/pi.alert/lib';
	  sub_filter '/php' '/pi.alert/php';		
     }
    }
``` 

3. Activate the new website by running the following command:

   `nginx -s reload` or `systemctl restart nginx`

4. Once NGINX restarts, you should be able to access the proxy website at https://pi.alert/pi.alert/

<br>

## Apache HTTP Configuration (Direct Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/pialert.conf.

2. In this file, paste the following code:

```
    <VirtualHost *:80>
         ServerName pi.alert
         ProxyPreserveHost On
         ProxyPass / http://localhost:20211/
         ProxyPassReverse / http://localhost:20211/
    </VirtualHost>
``` 

3. Activate the new website by running the following command:

   `a2ensite pialert` or `service apache2 reload`

4. Once Apache restarts, you should be able to access the proxy website at http://pi.alert/

<br>

## Apache HTTP Configuration (Sub Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/pialert.conf.

2. In this file, paste the following code:

```
    <VirtualHost *:80>
         ServerName pi.alert
         location ^~ /pi.alert/ {
               ProxyPreserveHost On
               ProxyPass / http://localhost:20211/
               ProxyPassReverse / http://localhost:20211/
         }
    </VirtualHost>
```   

3. Activate the new website by running the following command:

   `a2ensite pialert` or `service apache2 reload`

4. Once Apache restarts, you should be able to access the proxy website at http://pi.alert/

<br>

## Apache HTTPS Configuration (Direct Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/pialert.conf.

2. In this file, paste the following code:

```
    <VirtualHost *:443>
         ServerName pi.alert
         SSLEngine On
         SSLCertificateFile /etc/ssl/certs/pi.alert.pem
         SSLCertificateKeyFile /etc/ssl/private/pi.alert.key
         ProxyPreserveHost On
         ProxyPass / http://localhost:20211/
         ProxyPassReverse / http://localhost:20211/
    </VirtualHost>
```   

3. Activate the new website by running the following command:

    `a2ensite pialert` or `service apache2 reload`

4. Once Apache restarts, you should be able to access the proxy website at https://pi.alert/

<br>

## Apache HTTPS Configuration (Sub Path)

1. On your Apache server, create a new file called /etc/apache2/sites-available/pialert.conf.

2. In this file, paste the following code:
                            
```
	<VirtualHost *:443> 
        ServerName pi.alert
        SSLEngine On 
        SSLCertificateFile /etc/ssl/certs/pi.alert.pem
        SSLCertificateKeyFile /etc/ssl/private/pi.alert.key
        location ^~ /pi.alert/ {
              ProxyPreserveHost On
              ProxyPass / http://localhost:20211/
              ProxyPassReverse / http://localhost:20211/
        }
    </VirtualHost>
```       

3. Activate the new website by running the following command:

   `a2ensite pialert` or `service apache2 reload`

4. Once Apache restarts, you should be able to access the proxy website at https://pi.alert/pi.alert/

## Reverse proxy example by using LinuxServer's SWAG container.

> Submitted by [s33d1ing](https://github.com/s33d1ing). 🙏

## [linuxserver/swag](https://github.com/linuxserver/docker-swag)

In the SWAG container create `/config/nginx/proxy-confs/pialert.subfolder.conf` with the following contents:

``` nginx
## Version 2023/02/05
# make sure that your pialert container is named pialert
# pialert does not require a base url setting

# Since Pi.Alert uses a Host network, you may need to use the IP address of the system running Pi.Alert for $upstream_app.

location /pialert {
    return 301 $scheme://$host/pialert/;
}

location ^~ /pialert/ {
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

    set $upstream_app pialert;
    set $upstream_port 20211;
    set $upstream_proto http;

    proxy_pass $upstream_proto://$upstream_app:$upstream_port;
    proxy_set_header Accept-Encoding "";

    proxy_redirect ~^/(.*)$ /pialert/$1;
    rewrite ^/pialert/?(.*)$ /$1 break;

    sub_filter_once off;
    sub_filter_types *;

    sub_filter 'href="/' 'href="/pialert/';

    sub_filter '(?>$host)/css' '/pialert/css';
    sub_filter '(?>$host)/js'  '/pialert/js';

    sub_filter '/img' '/pialert/img';
    sub_filter '/lib' '/pialert/lib';
    sub_filter '/php' '/pialert/php';
}
```


## Traefik

> Submitted by [Isegrimm](https://github.com/Isegrimm) 🙏 (based on this [discussion](https://github.com/jokob-sk/Pi.Alert/discussions/449#discussioncomment-7281442))

Asuming the user already has a working Traefik setup, this is what's needed to make Pi.Alert work at a URL like www.domain.com/pialert/. 

Note: Everything in these configs assumes '**www.domain.com**' as your domainname and '**section31**' as an arbitrary name for your certificate setup. You will have to substitute these with your own.

Also, I use the prefix '**pialert**'. If you want to use another prefix, change it in these files: dynamic.toml and default.

Content of my yaml-file (this is the generic Traefik config, which defines which ports to listen on, redirect http to https and sets up the certificate process).
It also contains Authelia, which I use for authentication.
This part contains nothing specific to Pi.Alert.

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
Snippet of the dynamic.toml file (referenced in the yml-file above) that defines the config for Pi.Alert:
The following are self-defined keywords, everything else is traefik keywords:
- pialert-router
- pialert-service
- auth
- pialert-stripprefix


```toml
[http.routers]
  [http.routers.pialert-router]
    entryPoints = ["websecure"]
    rule = "Host(`www.domain.com`) && PathPrefix(`/pialert`)"
    service = "pialert-service"
    middlewares = "auth,pialert-stripprefix"
    [http.routers.pialert-router.tls]
       certResolver = "section31"
       [[http.routers.pialert-router.tls.domains]]
         main = "www.domain.com"

[http.services]
  [http.services.pialert-service]
    [[http.services.pialert-service.loadBalancer.servers]]
      url = "http://internal-ip-address:20211/"

[http.middlewares]
  [http.middlewares.auth.forwardAuth]
    address = "http://authelia:9091/api/verify?rd=https://www.domain.com/authelia/"
    trustForwardHeader = true
    authResponseHeaders = ["Remote-User", "Remote-Groups", "Remote-Name", "Remote-Email"]
  [http.middlewares.pialert-stripprefix.stripprefix]
    prefixes = "/pialert"
    forceSlash = false

```
To make Pi.Alert work with this setup I modified the default file at `/etc/nginx/sites-available/default` in the docker container by copying it to my local filesystem, adding the changes as specified by [cvc90](https://github.com/cvc90) and mounting the new file into the docker container, overwriting the original one. By mapping the file instead of changing the file in-place, the changes persist if an updated dockerimage is pulled. This is also a downside when the default file is updated, so I only use this as a temporary solution, until the dockerimage is updated with this change.

Default-file:

```
server {
    listen 80 default_server;
    root /var/www/html;
    index index.php;
    #rewrite /pialert/(.*) / permanent;
    add_header X-Forwarded-Prefix "/pialert" always;
    proxy_set_header X-Forwarded-Prefix "/pialert";

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

Mapping the updated file (on the local filesystem at `/appl/docker/pialert/default`) into the docker container:


```bash
docker run -d --rm --network=host \
  --name=pi.alert \
  -v /appl/docker/pialert/config:/home/pi/pialert/config \
  -v /appl/docker/pialert/db:/home/pi/pialert/db \
  -v /appl/docker/pialert/default:/etc/nginx/sites-available/default \
  -e TZ=Europe/Amsterdam \
  -e PORT=20211 \
  jokobsk/pi.alert:latest

```

