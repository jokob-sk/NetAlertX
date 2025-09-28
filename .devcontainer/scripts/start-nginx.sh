
#create /services/nginx directory for nginx system files

nginx -c "/services/nginx/nginx.conf" -g "daemon off;" 2>&1 >/app/log/app_front.log