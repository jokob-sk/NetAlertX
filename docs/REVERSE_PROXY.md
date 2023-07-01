## Reverse proxy configuration

Submitted by [s33d1ing](https://github.com/s33d1ing).


Reverse proxy example by using LinuxServer's SWAG container.

### nginx config


``` nginx
location /pialert {
    return 301 $scheme://$host/pialert/;
}

location ^~ /pialert/ {
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
    sub_filter '(?>$host)/img' '/pialert/img';
    sub_filter '(?>$host)/js'  '/pialert/js';
    sub_filter '(?>$host)/lib' '/pialert/lib';
    sub_filter '(?>$host)/php' '/pialert/php';
}
```