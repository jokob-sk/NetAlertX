# How to debug the Invalid JSON response error

Check the the HTTP response of the failing backend call by following these steps:

- Open developer console in your browser (usually, e. g. for Chrome, key F12 on the keyboard).
- Follow the steps in this screenshot:

![F12DeveloperConsole][F12DeveloperConsole]

- Copy the URL causing the error and enter it in the address bar of your browser directly and hit enter. The copied URLs could look something like this (notice the query strings at the end):
  - `http://<server>:20211/api/table_devices.json?nocache=1704141103121`


- Post the error response in the existing issue thread on GitHub or create a new issue and include the redacted response of the failing query.

For reference, the above queries should return results in the following format:

## First URL:

- Should yield a valid JSON file

## Second URL:

![array][array]

## Third URL:

![json][json]

You can copy and paste any JSON result (result of the First and Third query) into an online JSON checker, such as [this one](https://jsonchecker.com/) to check if it's valid.


[F12DeveloperConsole]:    ./img/DEBUG/Invalid_JSON_repsonse_debug.png           "F12DeveloperConsole"
[array]:                  ./img/DEBUG/array_result_example.png                  "array"
[json]:                   ./img/DEBUG/JSON_result_example.png                   "json"
