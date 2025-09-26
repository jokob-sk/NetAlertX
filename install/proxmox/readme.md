# NetAlertX Proxmox Installer

A comprehensive installer script for deploying NetAlertX on Proxmox VE (Debian-based) systems. This installer automates the complete setup including dependencies, NGINX configuration, systemd service, and security hardening.

## 🚀 Quick Start

### Prerequisites
- Proxmox
- Clean Debian 13 LXC with sufficient resources 
- Root access
- Internet connection
- A Network to scan might be helpful!

### Installation

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/install/proxmox/proxmox-install-netalertx.sh | bash
```

### Non-Interactive Installation
```bash
# Skip all prompts and use defaults
NETALERTX_ASSUME_YES=1 curl -fsSL https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/install/proxmox/proxmox-install-netalertx.sh | bash

# Custom port
PORT=8080 NETALERTX_ASSUME_YES=1 curl -fsSL https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/install/proxmox/proxmox-install-netalertx.sh | bash
```

## 📋 What This Installer Does

### System Dependencies
- **PHP 8.4** with FPM, SQLite3, cURL extensions
- **NGINX** with custom configuration
- **Python 3** with virtual environment
- **Network tools**: nmap, arp-scan, traceroute, mtr, speedtest-cli
- **Additional tools**: git, build-essential, avahi-daemon

### Security Features
- **Hardened permissions**: Proper user/group ownership
- **TMPFS mounts**: Log and API directories mounted as tmpfs for security
- **NGINX user**: Configured to run as www-data
- **Strict bash options**: Error handling and security

### Service Management
- **Systemd service**: Auto-start on boot with restart policies
- **Service monitoring**: Built-in health checks and logging
- **Dependency management**: Waits for network and NGINX

### Service Management
```bash
# Check service status
systemctl status netalertx

# View logs
journalctl -u netalertx -f

# Restart service
systemctl restart netalertx

# Stop service
systemctl stop netalertx
```

## 🌐 Access

After installation, access NetAlertX at:
```
http://[SERVER_IP]:[PORT]
```

## 🔒 Security Considerations

### TMPFS Mounts
- `/app/log` - Mounted as tmpfs (no persistent logs)
- `/app/api` - Mounted as tmpfs (temporary API data)

### File Permissions
- Application files: `www-data:www-data` with appropriate permissions
- NGINX runs as `www-data` user
- Log directories: Secure permissions with tmpfs

### Network Security
- NGINX configured for internal network access
- No external firewall rules added (configure manually if needed)

## 🛠️ Troubleshooting

### Common Issues

#### 403 Forbidden Error
```bash
# Check file permissions
ls -la /var/www/html/netalertx
ls -la /app/front

# Fix permissions
chown -R www-data:www-data /app/front
chmod -R 755 /app/front
```

#### Service Won't Start
```bash
# Check service status
systemctl status netalertx

# View detailed logs
journalctl -u netalertx --no-pager -l

# Check if port is in use
ss -tlnp | grep :20211
```

#### GraphQL Connection Issues
```bash
# Check API token in config
grep API_TOKEN /app/config/app.conf

# Verify GraphQL port
grep GRAPHQL_PORT /app/config/app.conf

# Check backend logs
tail -f /app/log/app.log
```

### Log Locations
- **Service logs**: `journalctl -u netalertx`
- **Application logs**: `/app/log/` (tmpfs)
- **NGINX logs**: `/var/log/nginx/`
- **PHP logs**: `/app/log/app.php_errors.log`

### Manual Service Start
If systemd service fails:
```bash
# Activate Python environment
source /opt/myenv/bin/activate

# Start manually
cd /app
python server/
```
or
```
./start.netalertx.sh
```
## 🔄 Updates

### Updating NetAlertX
```bash
# Stop service
systemctl stop netalertx

# Update from repository
cd /app
git pull origin main

# Restart service
systemctl start netalertx
```


## 📁 File Structure

```
/app/                          # Main application directory
├── front/                     # Web interface (symlinked to /var/www/html/netalertx)
├── server/                    # Python backend
├── config/                    # Configuration files
├── db/                        # Database files
├── log/                       # Log files (tmpfs)
├── api/                       # API files (tmpfs)
└── start.netalertx.sh        # Service startup script

/etc/systemd/system/
└── netalertx.service         # Systemd service definition

/etc/nginx/conf.d/
└── netalertx.conf            # NGINX configuration
```

## 🤝 Contributing
This installer will need a maintainer

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This installer was designed for a Proxmox LXC Debian 13 container. For other systems, please use the appropriate installer or manual installation instructions.

