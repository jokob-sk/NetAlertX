# How to debug the Invalid JSON response error

Check the the HTTP response of the failing backend call by following these steps:

- Open developer console in your browser (usually, e. g. for Chrome, key F12 on the keyboard).
- Follow the steps in this screenshot: 

![F12DeveloperConsole][F12DeveloperConsole]

- Copy the URL causing the error and enter it in the address bar of your browser directly and hit enter. The copied URLs could look something like this (notice the query strings at the end):
  - `http://<pialert URL>:20211/php/server/devices.php?action=getDevicesTotals`
  - `http://<pialert URL>:20211/php/server/devices.php?action=getDevicesList&status=all`

- Post the error response in the existing issue thread on GitHub or create a new issue and include the redacted response of the failing query.

For reference, the above queries should return results in the following format:

First URL:

![array][array]

Second URL:

![json][json]

You can copy and paste any JSON result (result of the second query) into an online JSON checker, such as [this one](https://jsonchecker.com/) to check if it's valid.


[F12DeveloperConsole]:    ./img/DEBUG/Invalid_JSON_repsonse_debug.png           "F12DeveloperConsole"
[array]:                  ./img/DEBUG/array_result_example.png                  "array"
[json]:                   ./img/DEBUG/JSON_result_example.png                   "json"
