# 📧 SMTP guides

## Using the GMX SMTP server

1. Go to your GMX account https://account.gmx.com
2. Under Security Options enable 2FA (Two-factor authentication)
3. Under Security Options generate an Application-specific password
4. Home -> Email Settings -> POP3 & IMAP -> Enable access to this account via POP3 and IMAP
5. In PiAlert specify these settings:

```python
    REPORT_MAIL=True
    SMTP_SERVER='mail.gmx.com'
    SMTP_PORT=465
    SMTP_USER='gmx_email@gmx.com'
    SMTP_PASS='<your Application-specific password>'
    SMTP_SKIP_TLS=True
    SMTP_FORCE_SSL=True
    SMTP_SKIP_LOGIN=False
    REPORT_FROM='gmx_email@gmx.com' # this has to be the same email as in SMTP_USER
    REPORT_TO='some_target_email@gmail.com'
```


## Using the Gmail SMTP server
    
1. Create an app password by following the instructions from Google, you need to Enable 2FA for this to work.
[https://support.google.com/accounts/answer/185833](https://support.google.com/accounts/answer/185833)

2. Specify the following settings:

```python
    REPORT_MAIL=True
    SMTP_SKIP_TLS=True
    SMTP_FORCE_SSL=True 
    SMTP_PORT=465
    SMTP_SERVER='smtp.gmail.com'
    SMTP_PASS='16-digit passcode from google'
    REPORT_TO='some_target_email@gmail.com'
```

