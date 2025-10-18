
This is the default filesystem for NetAlertX. It contains

- `/app` - The main application location.  This structure is where the source code (back, front and server directories) is copied and executed in read-only form. It also provides default structures for the working directories, such as: config, db, and log. All other directories are not required in the production image and are not tracked.
- `/build` - a place where services can be initialized during docker container build. This folder is copied in, executed near the end of the build before the system is locked down, and then deleted.  It is only available during build time.
- `/opt/venv/lib/python3.12/site-packages/aiofreebox` - this holds a certificate used by aiofreebox package, which interacts with freebox OS.
- `/services` - a directory where all scripts which control system executions are held
    - `/services/config` - a directory which holds all configuration files and `conf.d` folders used in the production image.
        - `/services/config/crond` - `crond` daemon config.
        - `/services/config/nginx` - `nginx` conf files.
        - `/services/config/php` - php conf file.
            - `/services/config/php/php-fpm.d` - a `.d` style directory, debugger parameters or other configurations can be dropped in here.
        - `/services/config/python-backend-extra-launch-parameters` - the contents of this file are added to launch params. It can be used to add debugging capabilities.
    - `/services/capcheck.sh` - This is run at startup to warn the user if the container does not hold required permissions to operate certain raw-packet tools.
    - `/services/healthcheck.sh` - The system healthcheck. This script tests the services and reports if something fails.
    - `/services/start-backend.sh` - The launcher for python services. This is called at startup by `entrypoint.sh`.
    - `/services/start-crond.sh` - The launcher for crond task scheduler. This is called at startup by `entrypoint.sh`.
    - `/services/start-nginx.sh` - The launcher for nginx frontend/website services. This is called at startup by `entrypoint.sh`.
    - `/services/start-php-fpm.sh` - The launcher for php-fpm, used to interpret php for the frontend website. This is called at startup by `entrypoint.sh`.
- `/entrypoint.sh` - Called at system startup to launch all services and servers required by NetAlertX.