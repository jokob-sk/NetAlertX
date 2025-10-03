#!/bin/bash


#Logging handled in nginx.conf
nginx -c "/services/nginx/nginx.conf" -g "daemon off;" 2>&1 >/dev/null 