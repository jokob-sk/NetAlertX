# Reverse Proxy Configuration

Reverse proxy example by using LinuxServer's SWAG container.

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




