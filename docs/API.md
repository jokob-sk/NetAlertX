## Where are API endpoints located

PiAlert comes with a simple API. These API endpoints are static files, which are updated during:

1) A notification event
2) TBD

In the container, these files are located under the `/home/pi/pialert/front/api/` folder and thus on the `<pialert_url>/api/<File name>` url.

You can access the following files:

  | File name | Description | 
  |----------------------|----------------------| 
  | `notification_text.txt` | The plain text version of the last notification. |
  | `notification_text.html` | The full HTML of the last email notification. |
  | `notification_json_final.json` | The json version of the last notification (e.g. used for webhooks - [sample JSON](https://github.com/jokob-sk/Pi.Alert/blob/main/back/webhook_json_sample.json)). |
  | `table_devices.json` | The current (at the time of the last update as mentioned above on this page) state of all of the available Devices detected by the app. |
  | `table_nmap_scan.json` | The current state of the discovered ports by the regular NMAP scans. |
  | `pholus_scan.json` | The latest state of the [pholus](https://github.com/jokob-sk/Pi.Alert/tree/main/pholus) (A multicast DNS and DNS Service Discovery Security Assessment Tool) scan results. |
  | `table_events_pending_alert.json` | The list of the unprocessed (pending) notification events. |
  
  Current/latest state of the aforementioned files depends on your settings.

