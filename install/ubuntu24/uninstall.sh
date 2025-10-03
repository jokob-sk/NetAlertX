#!/usr/bin/env bash
set -euo pipefail

  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Starting NetAlertX uninstallation for Ubuntu"
  echo "---------------------------------------------------------"
  echo

  if [[ $EUID -ne 0 ]]; then
    echo "[UNINSTALL] This script must be run as root. Please use 'sudo'."
    exit 1
  fi

  SYSTEMD_UNIT_FILE="/etc/systemd/system/netalertx.service"
  SYSTEMD_UNIT_DEFAULTS="/etc/default/netalertx"

  DEFAULT_INSTALL_DIR="/app"
  DEFAULT_INSTALL_SYSTEM_NAME="ubuntu24"
  DEFAULT_WEB_UI_DIR="/var/www/html/netalertx"
  DEFAULT_NGINX_CONF_FILE="netalertx.conf"
  DEFAULT_VENV_DIR="/opt/netalertx-python"
  DEFAULT_PHPVERSION="8.3"

  if [ -f "$SYSTEMD_UNIT_DEFAULTS" ]; then
    # shellcheck disable=SC1090
    source "$SYSTEMD_UNIT_DEFAULTS"
  fi

  INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
  INSTALL_SYSTEM_NAME="${INSTALL_SYSTEM_NAME:-$DEFAULT_INSTALL_SYSTEM_NAME}"
  INSTALLER_DIR="${INSTALLER_DIR:-${INSTALL_DIR}/install/${INSTALL_SYSTEM_NAME}}"
  WEB_UI_DIR="${WEB_UI_DIR:-$DEFAULT_WEB_UI_DIR}"
  NGINX_CONF_FILE="${NGINX_CONF_FILE:-$DEFAULT_NGINX_CONF_FILE}"
  NGINX_CONFIG_FILE="/etc/nginx/conf.d/${NGINX_CONF_FILE}"
  VENV_DIR="${VIRTUAL_ENV:-$DEFAULT_VENV_DIR}"
  PHPVERSION="${PHPVERSION:-$DEFAULT_PHPVERSION}"

  echo "[UNINSTALL] Target install dir : ${INSTALL_DIR}"
  echo "[UNINSTALL] Web UI location    : ${WEB_UI_DIR}"
  echo "[UNINSTALL] Nginx config file  : ${NGINX_CONFIG_FILE}"
  echo "[UNINSTALL] Python venv        : ${VENV_DIR}"
  echo

PURGE_DATA=false
PURGE_PACKAGES=false

for arg in "$@"; do
  case "$arg" in
    --purge-data)
      PURGE_DATA=true
      ;;
    --purge-packages)
      PURGE_PACKAGES=true
      ;;
    --help)
      cat <<'USAGE'
Usage: uninstall.sh [--purge-data] [--purge-packages]
  --purge-data       Remove the application directory without prompting.
  --purge-packages   Purge packages that were installed by install.sh without prompting.
USAGE
      exit 0
      ;;
    *)
      echo "[UNINSTALL] Unknown option: $arg" >&2
      echo "[UNINSTALL] Use --help to see available options." >&2
      exit 1
      ;;
  esac
done

  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Stopping services"
  echo "---------------------------------------------------------"
  systemctl stop netalertx 2>/dev/null || true
  systemctl disable netalertx 2>/dev/null || true
  systemctl reset-failed netalertx 2>/dev/null || true

  echo
  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Removing systemd unit and defaults"
  echo "---------------------------------------------------------"
  rm -f "$SYSTEMD_UNIT_FILE"
  rm -f "$SYSTEMD_UNIT_DEFAULTS"
  systemctl daemon-reload
  echo "[UNINSTALL] Systemd cleanup complete"

  echo
  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Unmounting tmpfs mounts"
  echo "---------------------------------------------------------"
  if command -v mountpoint >/dev/null 2>&1; then
    for mount_point in "${INSTALL_DIR}/log" "${INSTALL_DIR}/api"; do
      if [ -d "$mount_point" ] && mountpoint -q "$mount_point"; then
        umount "$mount_point" || true
        echo "[UNINSTALL] Unmounted ${mount_point}"
      fi
    done
  else
    echo "[UNINSTALL] mountpoint utility not available; skipping tmpfs checks."
  fi

  echo
  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Cleaning nginx and web artifacts"
  echo "---------------------------------------------------------"
  NEED_NGINX_RELOAD=false

  if [ -e "$WEB_UI_DIR" ]; then
    TARGET="$(readlink -f "$WEB_UI_DIR" 2>/dev/null || echo "$WEB_UI_DIR")"
    if [ "$TARGET" = "${INSTALL_DIR}/front" ]; then
      rm -rf "$WEB_UI_DIR"
      echo "[UNINSTALL] Removed web UI link ${WEB_UI_DIR}"
    fi
  fi

  if [ -e "$NGINX_CONFIG_FILE" ]; then
    TARGET="$(readlink -f "$NGINX_CONFIG_FILE" 2>/dev/null || echo "")"
    if [ -n "$TARGET" ] && [[ "$TARGET" == "${INSTALLER_DIR}/"* ]]; then
      rm -f "$NGINX_CONFIG_FILE"
      NEED_NGINX_RELOAD=true
      echo "[UNINSTALL] Removed nginx config ${NGINX_CONFIG_FILE}"
    elif grep -qi "netalertx" "$NGINX_CONFIG_FILE" 2>/dev/null; then
      rm -f "$NGINX_CONFIG_FILE"
      NEED_NGINX_RELOAD=true
      echo "[UNINSTALL] Removed nginx config ${NGINX_CONFIG_FILE}"
    fi
  fi

  if [ -f /etc/nginx/sites-available/default.bkp_netalertx ]; then
    if [ -e /etc/nginx/sites-enabled/default ]; then
      rm -f /etc/nginx/sites-enabled/default
    fi
    mv /etc/nginx/sites-available/default.bkp_netalertx /etc/nginx/sites-enabled/default
    NEED_NGINX_RELOAD=true
    echo "[UNINSTALL] Restored nginx default site"
  elif [ ! -e /etc/nginx/sites-enabled/default ] && [ -f /etc/nginx/sites-available/default ];
  then
    ln -s ../sites-available/default /etc/nginx/sites-enabled/default
    NEED_NGINX_RELOAD=true
    echo "[UNINSTALL] Re-enabled nginx default site"
  fi

  echo
  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Removing application files"
  echo "---------------------------------------------------------"

  if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "[UNINSTALL] Removed virtual environment ${VENV_DIR}"
  fi

  if [ -d "$INSTALL_DIR" ]; then
    if [ "$PURGE_DATA" = false ]; then
      if [ -t 0 ]; then
        echo "[UNINSTALL] ${INSTALL_DIR} contains NetAlertX binaries, config, and database."
        read -r -p "[UNINSTALL] Type 'purge' to delete it now, or press Enter to keep it:
  " answer
        if [ "$answer" = "purge" ]; then
          PURGE_DATA=true
        else
          echo "[UNINSTALL] Keeping ${INSTALL_DIR}"
        fi
      else
        echo "[UNINSTALL] Skipping removal of ${INSTALL_DIR}; rerun with --purge-data to
  delete it."
      fi
    fi

    if [ "$PURGE_DATA" = true ]; then
      if [[ "$INSTALL_DIR" == "/" ]]; then
        echo "[UNINSTALL] Refusing to remove root directory."
      else
        rm -rf "$INSTALL_DIR"
        echo "[UNINSTALL] Removed ${INSTALL_DIR}"
      fi
    fi
  fi

if [ "$NEED_NGINX_RELOAD" = true ] && command -v nginx >/dev/null 2>&1; then
    echo
    echo "---------------------------------------------------------"
    echo "[UNINSTALL] Reloading nginx"
    echo "---------------------------------------------------------"
    if nginx -t; then
      systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
    else
      echo "[UNINSTALL] nginx config test failed; please fix manually before reloading."
    fi
  fi

echo
echo "---------------------------------------------------------"
echo "[UNINSTALL] Package cleanup"
echo "---------------------------------------------------------"

PACKAGES_TO_PURGE=(
  git
  tini
  ca-certificates
  curl
  libwww-perl
  perl
  apt-utils
  cron
  build-essential
  sqlite3
  net-tools
  python3
  python3-venv
  python3-dev
  python3-pip
  dnsutils
  mtr
  arp-scan
  snmp
  iproute2
  nmap
  zip
  usbutils
  traceroute
  nbtscan
  avahi-daemon
  avahi-utils
  nginx-core
  php${PHPVERSION}
  php${PHPVERSION}-sqlite3
  php
  php-fpm
  php-cgi
  php${PHPVERSION}-fpm
  php-sqlite3
  php-curl
  php-cli
)

if command -v apt-get >/dev/null 2>&1; then
  if [ "$PURGE_PACKAGES" = false ]; then
    if [ -t 0 ]; then
      echo "[UNINSTALL] The installer may have added these packages:"
      printf '  - %s\n' "${PACKAGES_TO_PURGE[@]}"
      echo "[UNINSTALL] Removing them can affect other applications that rely on them."
      read -r -p "[UNINSTALL] Type 'purge' to remove these packages now, or press Enter to keep them: " package_answer
      if [ "$package_answer" = "purge" ]; then
        PURGE_PACKAGES=true
      else
        echo "[UNINSTALL] Keeping installed packages."
      fi
    else
      echo "[UNINSTALL] Packages installed by the original script were left in place."
      echo "[UNINSTALL] Re-run with --purge-packages to remove them automatically."
    fi
  fi

  if [ "$PURGE_PACKAGES" = true ]; then
    echo "[UNINSTALL] Removing installer packages via apt-get purge."
    if ! apt-get purge -y "${PACKAGES_TO_PURGE[@]}"; then
      echo "[UNINSTALL] Failed to purge some packages; please review the output above." >&2
    else
      apt-get autoremove -y
      echo "[UNINSTALL] Package purge complete."
    fi
  fi
else
  echo "[UNINSTALL] apt-get not found; skipping package removal."
fi

  echo
  echo "---------------------------------------------------------"
  echo "[UNINSTALL] NetAlertX removal complete"
  echo "---------------------------------------------------------"
  echo "[UNINSTALL] Thank you for using NetAlertX."
