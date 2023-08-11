## Overview

A simple script-based plugin for setting the password. 

### Usage

- Head to **Settings** > **UI password** to adjust the default values.

### Notes

- The plugin is executed on the `RUN` type `before_config_save` so it's possible to update the `pialert.conf` file before the data is loaded into the app. 
- The executed command is stored in the `CMD` setting: `/home/pi/pialert/back/pialert-cli set_password {password}`
- The `{password}` parameter is replaced via the parameter and setting below:

```json
  ...
"params" : [
    {
        "name"  : "password",
        "type"  : "setting",
        "value" : "SETPWD_password"
    }
  ], 

  ...
  {
    "function": "password",
    "type": "password",
    "maxLength": 50,
    "default_value": "123456",
    "options": [],
    "localized": ["name", "description"],
    "name": [
      {
        "language_code": "en_us",
        "string": "Password"
      }
    ],
    "description": [
      {
        "language_code": "en_us",
        "string": "The default password is <code>123456</code>. To change the password run <code>/home/pi/pialert/back/pialert-cli set_password {password}</code> in the container"
      }
    ]
  }


```
