## Descripción general

Un plugin simple basado en script para configurar la contraseña.

### Uso

- Dirígete a **Configuración** > **Contraseña de UI** para ajustar los valores predeterminados.

### Notas

- El complemento se ejecuta `RUN` con en el tipo `before_config_save`, por lo que es posible actualizar el archivo `pialert.conf` antes de que los datos se carguen en la aplicación.
- El comando ejecutado se almacena en la configuración `CMD`: `/home/pi/pialert/back/pialert-cli set_password {contraseña}`
- El parámetro `{contraseña}` se reemplaza mediante el parámetro y la configuración a continuación:

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
