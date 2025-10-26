# 📧 SMTP server guides

The SMTP plugin supports any SMTP server. Here are some commonly used services to help speed up your configuration.

> [!NOTE]
> If you are using a self hosted SMTP server ssh into the container and verify (e.g. via ping) that your server is reachable from within the NetAlertX container. See also how to ssh into the container if you are running it as a [Home Assistant](./HOME_ASSISTANT.md) addon. 

## Gmail
    
1. Create an app password by following the instructions from Google, you need to Enable 2FA for this to work.
[https://support.google.com/accounts/answer/185833](https://support.google.com/accounts/answer/185833)

2. Specify the following settings:

```python
    SMTP_RUN='on_notification'
    SMTP_SKIP_TLS=True
    SMTP_FORCE_SSL=True 
    SMTP_PORT=465
    SMTP_SERVER='smtp.gmail.com'
    SMTP_PASS='16-digit passcode from google'
    SMTP_REPORT_TO='some_target_email@gmail.com'
```

## Brevo

Brevo allows for 300 free emails per day as of time of writing. 

1. Create an account on Brevo: https://www.brevo.com/free-smtp-server/
2. Click your name -> SMTP & API
3. Click Generate a new SMTP key
4. Save the details and fill in the NetAlertX settings as below.

```python
SMTP_SERVER='smtp-relay.brevo.com'
SMTP_PORT=587
SMTP_SKIP_LOGIN=False
SMTP_USER='user@email.com'
SMTP_PASS='xsmtpsib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxx'
SMTP_SKIP_TLS=False
SMTP_FORCE_SSL=False
SMTP_REPORT_TO='some_target_email@gmail.com'
SMTP_REPORT_FROM='NetAlertX <user@email.com>'
```

## GMX

1. Go to your GMX account https://account.gmx.com
2. Under Security Options enable 2FA (Two-factor authentication)
3. Under Security Options generate an Application-specific password
4. Home -> Email Settings -> POP3 & IMAP -> Enable access to this account via POP3 and IMAP
5. In NetAlertX specify these settings:

```python
    SMTP_RUN='on_notification'
    SMTP_SERVER='mail.gmx.com'
    SMTP_PORT=465
    SMTP_USER='gmx_email@gmx.com'
    SMTP_PASS='<your Application-specific password>'
    SMTP_SKIP_TLS=True
    SMTP_FORCE_SSL=True
    SMTP_SKIP_LOGIN=False
    SMTP_REPORT_FROM='gmx_email@gmx.com' # this has to be the same email as in SMTP_USER
    SMTP_REPORT_TO='some_target_email@gmail.com'
```

