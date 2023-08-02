# Reverse Proxy Configuration

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




