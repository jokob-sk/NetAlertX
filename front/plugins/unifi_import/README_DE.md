## Übersicht

Dieses Plugin imporiert die Geräte von einem UNIFI Controller.

### Verwendung

Die folgenden Einstellungen im Einstelllungen-Abschnitt in PiAlert setzen:

- `UNFIMP_username` - Benutzername welcher zum Einloggen beim UNIFI-Controller verwendet wird.
- `UNFIMP_password` - Passwort welches zum Einloggen beim UNIFI-Controller verwendet wird.
- `UNFIMP_host` - Der Host (IP) auf welchem der UNIFI-Controller läuft (ohne http://).
- `UNFIMP_sites` - Namen der Standorite (normalerweise 'default', um sicherzugehen, die URL im UniFi Controller - UI überprüfen. Die Standort-ID ist dieser Teil der URL: `https://192.168.1.1:8443/manage/site/Hier-ist-die-Standort-ID/settings/`).
- `UNFIMP_port` - Normalerweise 8443.

### Notizen

- Wird aktuell nur für den Import von Geräten, aber nicht deren Status, Typ oder Netzwerkkarte, verwendet.
- Es wird empfohlen einen Benutzer nur mit Leseberechtigungen im UniFi-Controller zu verwenden.
