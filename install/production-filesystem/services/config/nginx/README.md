Nginx's active configuration lives in /tmp/nginx/active-config by default when the container runs read-only without a bind mount.

Mounting a writable directory at /tmp/nginx/active-config allows the entrypoint to rewrite the nginx template so LISTEN_ADDR and PORT environment overrides take effect.

The act of running /services/start-nginx.sh writes a new nginx.conf file, using envsubst, then starts nginx based on the parameters in that file.

Defaults: 
LISTEN_ADDR=0.0.0.0
PORT=20211