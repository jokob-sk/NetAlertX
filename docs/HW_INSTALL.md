# How to install NetAlertX on the server hardware

To download and install NetAlertX on the hardware/server directly use the `curl` or `wget` commands at the bottom of this page.

> [!NOTE]
> This is an Experimental feature 🧪 and it relies on community support.
>
> Looking for maintainers for this installation method 🙂
>
> There is no guarantee that the install script or any other script will gracefully handle other installed software.
> Data loss is a possibility, **it is recommended to install NetAlertX using the supplied Docker image**.

A warning to the installation method below: Piping to bash is [controversial](https://pi-hole.net/2016/07/25/curling-and-piping-to-bash) and may
be dangerous, as you cannot see the code that's about to be executed on your system.

Alternatively you can download the installation script `install/install.debian.sh` from the repository and check the code yourself (beware other scripts are
downloaded too - only from this repo).

NetAlertX will be installed in `/app` and run on port number `20211`.

Some facts about what and where something will be changed/installed by the HW install setup (may not contain everything!):

- `/app` directory will be deleted and newly created
- `/app` will contain the whole repository (downloaded by `install/install.debian.sh`)
- The default NGINX site `/etc/nginx/sites-enabled/default` will be disabled (sym-link deleted or backed up to `sites-available`)
- `/var/www/html/netalertx` directory will be deleted and newly created
- `/etc/nginx/conf.d/netalertx.conf` will be sym-linked to `/app/install/netalertx.debian.conf`
- Some files (IEEE device vendors info, ...) will be created in the directory where the installation script is executed

## Limitations

- No system service is provided. NetAlertX must be started using `/app/install/start.debian.sh`.
- No checks for other running software is done.
- Only tested to work on Debian Bookworm (Debian 12).
- **EXPERIMENTAL** and not recommended way to install NetAlertX.

## 📥 Installation via CURL

```bash
curl -o install.debian.sh https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/install/install.debian.sh && sudo chmod +x install.debian.sh && sudo ./install.debian.sh
```

## 📥 Installation via WGET

```bash
wget https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/install/install.debian.sh -O install.debian.sh && sudo chmod +x install.debian.sh && sudo ./install.debian.sh
```

These commands will download the `install.debian.sh` script from the GitHub repository, make it executable with `chmod`, and then run it using `./install.debian.sh`.

Make sure you have the necessary permissions to execute the script.
