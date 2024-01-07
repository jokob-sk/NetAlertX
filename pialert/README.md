# Pi.Alert modules

The original pilaert.py code is now moved to this new folder and split into different modules.

| Module | Description |
|--------|-----------|
|```__main__.py```| The MAIN program of Pi.Alert|
|```__init__.py```| an empty init file|
|```README.md```| this readme file|
|```../front/plugins ```| a folder containing all [plugins](/front/plugins/) that publish notifications or scan for devices|
|```api.py```| updating the API endpoints with the relevant data. |
|```appevent.py```| TBC |
|```const.py```| A place to define the constants for Pi.Alert like log path or config path.|
|```conf.py```| conf.py holds the configuration variables and makes them available for all modules. It is also the <b>workaround</b> for global variables that need to be resolved at some point|
|```database.py```| This module connects to the DB, makes sure the DB is up to date and defines some standard queries and interfaces. |
|```device.py```| The device module looks after the devices and saves the scan results into the devices |
|```flows.py```| TBC |
|```helper.py```| Helper as the name suggest contains multiple little functions and methods used in many of the other modules and helps keep things clean |
|```initialise.py```| Initiatlise sets up the environment and makes everything ready to go |
|```logger.py```| Logger is there the keep all the logs organised and looking identical. |
|```networscan.py```| Networkscan collects teh scan results (maybe to merge with `reporting.py`) |
|```notification.py```| Creates and handles the notification object and generates ther HTML and text variants of the message |
|```plugin.py```| This is where the plugins get integrated into the backend of Pi.Alert |
|```plugin_utils.py```| Helper utilities for `plugin.py` |
|```reporting.py```| Reporting collects the data for the notification reports |
|```scheduler.py```| All things scheduling |





