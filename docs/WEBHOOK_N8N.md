### Create a simple n8n workflow

![n8n workflow](/docs/img/WEBHOOK_N8N/n8n_workflow.png)

### Specify your email template 
See [sample JSON](https://github.com/jokob-sk/Pi.Alert/blob/main/back/webhook_json_sample.json) if you want to see the JSON paths used in the email template below
![Email template](/docs/img/WEBHOOK_N8N/n8n_send_email_settings.png)

```
Events count: {{ $json["body"]["attachments"][0]["text"]["events"].length }}
New devices count: {{ $json["body"]["attachments"][0]["text"]["new_devices"].length }}
```

### Get your webhook in n8n
![n8n webhook URL](/docs/img/WEBHOOK_N8N/n8n_webhook_settings.png)

### Configure PiAlert to point to the above URL
![PiAlert config](/docs/img/WEBHOOK_N8N/Webhook_settings.png)
