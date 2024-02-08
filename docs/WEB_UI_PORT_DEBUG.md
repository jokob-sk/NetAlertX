# Debugging inaccessible UI

When opening an issue please :

1. Include a screenshot of what you see when accessing `HTTP://<your rpi IP>/20211` (or your custom port)
1. [Follow steps 1, 2, 3, 4  on this page](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/DEBUG_TIPS.md) 
1. Execute the following in the container to see the processes and their ports and submit a screenshot of the result:
   1. `sudo apt-get install lsof`
   1. `sudo lsof -i`


![lsof ports](/docs/img/WEB_UI_PORT_DEBUG/container_port.png)