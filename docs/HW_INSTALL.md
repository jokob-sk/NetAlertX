# How to install PiAlert on the server hardware

To download and install PiAlert on the hardware/server directly use `curl` or `wget` commands.

> [!NOTE]
> This is an Experimental feature 🧪 and it relies on community support.
>
> There is no guarantee that the install script or any other script will gracefully handle other installed software.
> Data loss is a possibility, **it is recommended to install PiAlert using the supplied Docker image**.

A warning to the installation method below: Piping to bash is [controversial](https://pi-hole.net/2016/07/25/curling-and-piping-to-bash) and may
be dangerous, as you cannot see the code that's about to be executed on your system.

Alternatively you can download the installation script `install/install.sh` from the repository and check the code yourself (beware other scripts are
downloaded too - only from this repo).

PiAlert will be installed in `home/pi/pialert/` and run on port number `20211`.

Some facts about what and where something will be changed/installed by the HW install setup (may not contain everything!):

- `/home/pi/pialert` directory will be deleted and newly created
- `/home/pi/pialert` will contain the whole repository (downloaded by `install/install.sh`)
- The default NGINX site `/etc/nginx/sites-enabled/default` will be disabled (sym-link deleted or backed up to `sites-available`)
- `/var/www/html/pialert` directory will be deleted and newly created
- `/etc/nginx/conf.d/pialert.conf` will be sym-linked to `/home/pi/pialert/install/pialert.conf`
- Some files (IEEE device vendors info, ...) will be created in the directory where the installation script is executed

## Limitations

- No system service is provided. PiAlert must be started using `/home/pi/pialert/dockerfiles/start.sh`.
- No checks for other running software is done.
- Only tested to work on Debian Bookworm (Debian 12).
- **EXPERIMENTAL** and not recommended way to install PiAlert.

## CURL

```bash
curl -o install.sh https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/install/install.sh && sudo chmod +x install.sh && sudo ./install.sh
```

## WGET

```bash
wget https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/install/install.sh -O install.sh && sudo chmod +x install.sh && sudo ./install.sh
```

These commands will download the `install.sh` script from the GitHub repository, make it executable with `chmod`, and then run it using `./install.sh`.

Make sure you have the necessary permissions to execute the script.
