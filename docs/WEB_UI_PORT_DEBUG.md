# Debugging inaccessible UI

## 1. Port conflicts

When opening an issue please:

1. Include a screenshot of what you see when accessing `HTTP://<your rpi IP>/20211` (or your custom port)
1. [Follow steps 1, 2, 3, 4  on this page](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_TIPS.md) 
1. Execute the following in the container to see the processes and their ports and submit a screenshot of the result:
   1. `sudo apk add lsof`
   1. `sudo lsof -i`
1. Try running the `nginx` command in the container
   1. if you get `nginx: [emerg] bind() to 0.0.0.0:20211 failed (98: Address in use)` try using a different port number


![lsof ports](/docs/img/WEB_UI_PORT_DEBUG/container_port.png)

## 2. JavaScript issues 

Check for browser console (F12 browser dev console) errors + check different browsers.


## 3. Clear the app cache and cached JavaScript files

Refresh the browser cache (usually shoft + refresh), try a private window, or different browsers. Please also refresh the app cache by clicking the 🔃 (reload) button in the header of the application. 

## 4. Disable proxy

If you have any reverse proxy or similar, try disabling it. 

## 5. Post your docker start details

If you haven't, post your docker compose/run command.

## 6. Check for errors in your PHP/NGINX error logs

In the container execute:

`cat /var/log/nginx/error.log`

`cat /app/front/log/app.php_errors.log`


## 7. Make sure permissions are correct

> [!TIP]
> You can try to start the container without mapping the `/app/config` and `/app/db` dirs and if the UI shows up then the issue is most likely related to your file system permissions or file ownership. 

Please read the [Permissions troubleshooting guide](/docs/FILE_PERMISSIONS.md) and provide a screesnhot of the permissions and ownership in the `/app/db` and `app/config` directories. 