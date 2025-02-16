# Securing your NetAlertX instance

NetAlertX is an execution framework. In order to run scanners and plugins, the application has to have access to privileged system resources. It is not recommended to expose NetAlertX to the internet without taking basic security precautions. It is highly recommended to use a VPN to access the application and to set up a password for the web interface before exposing the UI online.

## VPN

VPNs allow you to securely access your NetAlertX instance from remote locations without exposing it to the internet. A VPN encrypts your connection and prevents unauthorized access.

### Tailscale as an Alternative

If setting up a traditional VPN is not ideal, you can use [Tailscale](https://tailscale.com/) as an easy alternative. Tailscale creates a secure, encrypted connection between your devices without complex configuration. Since NetAlertX is designed to be run on private networks, Tailscale can provide a simple way to securely connect to your instance from anywhere.

## Setting a Password

By default, NetAlertX does not enforce authentication, but it is highly recommended to set a password before exposing the web interface.

Configure `SETPWD_enable_password` to `true` and enter your password in `SETPWD_password`. When enabled, a login dialog is displayed. If facing issues, you can always disable the login by setting `SETPWD_enable_password=false` in your `app.conf` file.

- The default password is `123456`.  
- Passwords are stored as SHA256 hashes for security.  

## Additional Security Measures

- **Firewall Rules**: Ensure that only trusted IPs can access the NetAlertX instance.  
- **Limit Plugin Permissions**: Only enable the plugins necessary for your setup.  
- **Keep Software Updated**: Regularly update NetAlertX to receive the latest security patches.  
- **Use Read-Only API Keys**: If exposing APIs, limit privileges with read-only keys where applicable.  

By following these security recommendations, you can help protect your NetAlertX instance from unauthorized access and potential misuse.
