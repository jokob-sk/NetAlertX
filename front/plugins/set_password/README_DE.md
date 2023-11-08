## Übersicht

Ein Plugin zum Setzen des Passworts beim Applikationsstart.

### Verwendung

- In **Einstellungen** > **Passwort setzen** die Standardwerte anpassen.

### Notizen

- Das Plugin wird mit dem `RUN`-Type `before_config_save` ausgeführt, daher ist es möglich die `pialert.conf` zu aktualisieren bevor die Daten in die Applikation geladen werden.
- Der ausgeführte Befehl ist in der `CMD`-Einstellung gespeichert: `/home/pi/pialert/back/pialert-cli set_password {password}`
- Der `{password}`-Platzhalter wird ausgetauscht mit dem Parameter und den Einstellungen:

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
