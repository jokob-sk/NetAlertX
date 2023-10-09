## Übersicht

Ein Plugin zum Importieren von nicht erkennbaren Geräten aus einer Datei. Das Plugin findet Verwendung, wenn "dumme" Netzwerkkomponenten (z.B. Unmanaged Hubs/Switches) zur Netzwerkansicht hinzugefügt werden sollen. Möglicherweise gibt es weitere Anwendungsfälle, bitte informiert uns darüber.

### Verwendung

- Einstellungen aufrufen und Nicht erkennbare Geräte in der Liste der Plugins finden
- Plugin aktivieren, indem der `RUN`-Parameter von `disabled` zu `once` oder `always_after_scan` geändert wird
- Gerätenamen der Liste hinzufügen (Beispieleintrag zuerst entfernen)
- SPEICHERN
- Auf Abschluss des nächsten Scans warten

#### Beispiele

Einstellungen:
![settings](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/52883307-19a5-4602-b13a-9825461f6cc4)

Resultat:
![devices](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/9f7659e7-75a8-4ae9-9f5f-781bdbcbc949)

Erlaubt nicht erkennbare Geräte wie Hubs, Switches oder APs in der Netzwerkansicht:
![network](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/b5ccc3b3-f5fd-4f5b-b0f0-e4e637c6da33)

### Bekannte Einschränkungen

- Nicht erkennbare Geräte erscheinen immer als Offline. Pi.Alert kann diese Geräte nicht erkennen (wie erwartet).
- Alle IPs werden auf 0.0.0.0 gesetzt, daher kann es sein, dass das "Zufällige MAC"-Icon erscheint
