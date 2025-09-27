
#create /services/nginx directory for nginx system files
sudo install -d /services/nginx -m 755 -o netalertx -g netalertx
sudo install -d /services/nginx -m 755 -o netalertx -g netalertx
sudo chown -R netalertx:netalertx /var/lib/nginx

cp /workspaces/NetAlertX/install/alpine-docker/app/services/nginx/nginx.conf /services/nginx/nginx.conf
sed -i 's|/app/services/nginx/netalertx.conf|/services/nginx/netalertx.conf|' /services/nginx/nginx.conf
cp /workspaces/NetAlertX/install/alpine-docker/app/services/nginx/netalertx.conf /services/nginx/netalertx.conf
cp /workspaces/NetAlertX/install/alpine-docker/app/services/nginx/fastcgi_params /services/nginx/fastcgi_params
nginx -c "/services/nginx/nginx.conf" -g "daemon off;" 2>&1 >/app/log/app_front.log