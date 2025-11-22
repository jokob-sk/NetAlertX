#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetAlertX-New-Devices-Checkmk-Script

Dieses Skript ruft die Liste aller Devices aus NetAlertX ab, indem es innerhalb
des Docker-Containers "NetAlertX" die Datei table_devices.json aus dem API-Verzeichnis
ausliest (standardmäßig /tmp/api, konfigurierbar via NETALERTX_API).
Anschließend wird geprüft, ob neue Geräte vorhanden sind (devIsNew == 1).
Falls ja, wird ein Warning-Zustand gemeldet, sonst OK.

Checkmk-Local-Check-Format:
  <status> <service_name> <perfdata> <message>
Siehe: https://docs.checkmk.com/latest/de/localchecks.html
"""

import subprocess
import json
import os


def check_new_devices():
    # Get API path from environment variable, fallback to /tmp/api
    api_path = os.environ.get('NETALERTX_API', '/tmp/api')
    table_devices_path = f'{api_path}/table_devices.json'

    try:
        # Rufe die JSON-Datei aus dem Docker-Container ab
        result = subprocess.run(
            ['docker', 'exec', 'NetAlertX', 'cat', table_devices_path],
            capture_output=True,
            text=True,
            check=True
        )
        data_str = result.stdout
    except subprocess.CalledProcessError as e:
        # Wenn der Docker-Command fehlschlägt -> UNKNOWN (3)
        print(f"3 NetAlertX_New_Devices - UNKNOWN - Docker command failed: {e}")
        return
    except Exception as e:
        # Allgemeiner Fehler -> UNKNOWN
        print(f"3 NetAlertX_New_Devices - UNKNOWN - Error while running docker command: {e}")
        return

    # JSON-Daten laden
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError as e:
        # Wenn das JSON nicht gelesen werden kann -> UNKNOWN
        print(f"3 NetAlertX_New_Devices - UNKNOWN - JSON decode error: {e}")
        return

    # Prüfen, ob das 'data'-Attribut vorhanden ist
    if "data" not in data:
        print("3 NetAlertX_New_Devices - UNKNOWN - Unexpected JSON format (no 'data' key).")
        return

    new_devices = []
    for device in data["data"]:
        # Prüfen, ob das Attribut 'devIsNew' existiert und == 1 ist
        if "devIsNew" in device and device["devIsNew"] == 1:
            new_devices.append(device)

    # Wenn keine neuen Geräte gefunden
    if len(new_devices) == 0:
        # Status 0 = OK
        print("0 NetAlertX_New_Devices - OK - No new devices found")
    else:
        # Status 1 = WARNING
        device_list_str = ", ".join(
            f"{dev.get('devName', 'UnknownName')}({dev.get('devMac', 'UnknownMAC')}) IP:{dev.get('devLastIP', 'UnknownIP')}"
            for dev in new_devices
        )
        print(f"1 NetAlertX_New_Devices - WARNING - Found {len(new_devices)} new device(s): {device_list_str}")


if __name__ == "__main__":
    check_new_devices()
