# Pi.Alert all split into modules

I am trying to split this big original file into modules and gives me some nice challanges to solve.
Since the original code is all in one file, the original author has taken quite some shortcuts by defining lots of variables as global !!
These need to be changed now.

Here is the main structure

| Module | Description |
|--------|-----------|
|pialert.py | The MAIN program of Pi.Alert|
|const.py | A place to define the constants for Pi.Alert like log path or config path.|
|const.py| const.py holds the configuration variables and makes them availabe for all modules. It is also the <b>workaround</b> for the global variables until I can work them out|
|api.py| |
