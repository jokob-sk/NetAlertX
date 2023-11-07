# Pi.Alert modules

The original pilaert.py code is now moved to this new folder and split into different modules.

| Module | Description |
|--------|-----------|
|```__main__.py```| The MAIN program of Pi.Alert|
|```__init__.py```| an empty init file|
|```README.md```| this readme file|
|**publishers**| a folder containing all modules used to publish the results|
|```api.py```| updating the API endpoints with the relevant data. (Should move to publishers)|
|```const.py```| A place to define the constants for Pi.Alert like log path or config path.|
|```conf.py```| conf.py holds the configuration variables and makes them available for all modules. It is also the <b>workaround</b> for global variables that need to be resolved at some point|
|```database.py```| This module connects to the DB, makes sure the DB is up to date and defines some standard queries and interfaces. |
|```device.py```| The device module looks after the devices and saves the scan results into the devices |
|```helper.py```| Helper as the name suggest contains multiple little functions and methods used in many of the other modules and helps keep things clean |
|```initialise.py```| Initiatlise sets up the environment and makes everything ready to go |
|```logger.py```| Logger is there the keep all the logs organised and looking identical. |
|```networscan.py```| Networkscan orchestrates the actual scanning of the network, calling the individual scanners and managing the results |
|```plugin.py```| This is where the plugins get integrated into the backend of Pi.Alert |
|```reporting.py```| Reporting generates the email, html and json reports to be sent by the publishers |
|```scheduler.py```| All things scheduling |





