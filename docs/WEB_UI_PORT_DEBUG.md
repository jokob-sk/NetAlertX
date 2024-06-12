# Debugging inaccessible UI

When opening an issue please:

1. Include a screenshot of what you see when accessing `HTTP://<your rpi IP>/20211` (or your custom port)
1. [Follow steps 1, 2, 3, 4  on this page](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_TIPS.md) 
1. Execute the following in the container to see the processes and their ports and submit a screenshot of the result:
   1. `sudo apt-get install lsof`
   1. `sudo lsof -i`
1. Try running the `nginx` command in the container
   1. if you get `nginx: [emerg] bind() to 0.0.0.0:20211 failed (98: Address in use)` try using a different port number


![lsof ports](/docs/img/WEB_UI_PORT_DEBUG/container_port.png)