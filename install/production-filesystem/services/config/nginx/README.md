Nginx's conf is in /services/config/nginx/conf.active.  This is the default configuration when run as a read-only container without a mount. 

With a tmpfs mount on /services/config/nginx/conf.active, the nginx template will be rewritten to allow ENV customization of listen address and port.

The act of running /services/start-nginx.sh writes a new nginx.conf file, using envsubst, then starts nginx based on the parameters in that file.

Defaults: 
LISTEN_ADDR=0.0.0.0
PORT=20211