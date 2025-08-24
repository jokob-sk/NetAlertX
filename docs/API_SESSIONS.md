# SEssions API Endpoints

Track device connection sessions.

* **POST** `/sessions/create` → Create a new session

  ```json
  { "mac": "AA:BB:CC:DD:EE:FF", "ip": "192.168.1.10", "start_time": "2025-08-01T10:00:00" }
  ```
* **DELETE** `/sessions/delete` → Delete session by MAC

  ```json
  { "mac": "AA:BB:CC:DD:EE:FF" }
  ```
* **GET** `/sessions/list?mac=<mac>&start_date=2025-08-01&end_date=2025-08-21` → List sessions
* **GET** `/sessions/calendar?start=2025-08-01&end=2025-08-21` → Calendar view of sessions
* **GET** `/sessions/<mac>?period=1 day` → Sessions for a device
* **GET** `/sessions/session-events?type=all&period=7 days` → Session events summary