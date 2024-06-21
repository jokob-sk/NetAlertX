## Development environemnt set up

>[!NOTE]
> Replace `/development` with the path where your code files will be stored. The default container name is `netalertx` so there might be a conflict with your running containers.

## 1. Download the code:

- `mkdir /development`
- `cd /development && git clone https://github.com/jokob-sk/NetAlertX.git`

## 2. Create a DEV .env_dev file

`touch /development/.env_dev && sudo nano /development/.env_dev`

The file content should be following, with your custom values.

```yaml
#--------------------------------
#NETALERTX
#--------------------------------
TZ=Europe/Berlin
PORT=22222    # make sure this port is unique on your whole network
DEV_LOCATION=/development/NetAlertX
APP_DATA_LOCATION=/volume/docker_appdata
# ALWAYS_FRESH_INSTALL=true # uncommenting this will always delete the content of /config and /db dirs on boot to simulate a fresh install
```

## 3. Create /db and /config dirs 

Create a folder `netalertx` in the `APP_DATA_LOCATION` (in this example in `/volume/docker_appdata`) with 2 subfolders `db` and `config`. 

- `mkdir /volume/docker_appdata/netalertx`
- `mkdir /volume/docker_appdata/netalertx/db`
- `mkdir /volume/docker_appdata/netalertx/config`

## 4. Run the container

- `cd /development/NetAlertX &&  sudo docker-compose --env-file ../.env_dev `

You can then modify the python script without restarting/rebuilding the container every time. Additionally, you can trigger a plugin run via the UI:

![image](https://github.com/jokob-sk/NetAlertX/assets/96159884/3cbf2748-03c8-49e7-b801-f38c7755246b)


## 💡 Tips

A quick cheat sheet of useful commands. 

### Removing the container and image 

A command to stop, remove the container and the image (replace `netalertx` and `netalertx-netalertx` with the appropriate values)

- `sudo docker container stop netalertx ; sudo docker container rm netalertx ; sudo docker image rm netalertx-netalertx`

### Restart hanging python script

SSH into the container and kill & restart the main script loop 

- `sudo docker exec -it netalertx /bin/bash`
- `pkill -f "python /app/server" && python /app/server & `




