## Use the Gmail SMTP server
    
1) Create an app password by following the instructions from Google, you need to Enable 2FA for this to work.
[https://support.google.com/accounts/answer/185833](https://support.google.com/accounts/answer/185833)

2) Specify the following settings:

```python
    SMTP_SKIP_TLS=True
    SMTP_FORCE_SSL=True 
    SMTP_PORT=465
    SMTP_SERVER='smtp.gmail.com'
    SMTP_PASS='16-digit passcode from google'
```

