#!/usr/bin/env bash

echo "---------------------------------------------------------"
echo "[INSTALL]                                  Run install.sh"
echo "---------------------------------------------------------"

# Set environment variables
INSTALL_DIR=/home/pi  # Specify the installation directory here

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi

# Prepare the environment
apt-get update
apt-get install sudo -y

# Install Git
apt-get install -y git

# Clean the directory
rm -R $INSTALL_DIR/pialert

# Clone the application repository
git clone https://github.com/jokob-sk/Pi.Alert "$INSTALL_DIR/pialert"

# Check for buildtimestamp.txt existence, otherwise create it
if [ ! -f $INSTALL_DIR/pialert/front/buildtimestamp.txt ]; then
  date +%s > $INSTALL_DIR/pialert/front/buildtimestamp.txt
fi

# Start PiAlert
"$INSTALL_DIR/pialert/dockerfiles/start.sh"
