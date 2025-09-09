#!/usr/bin/env bash

# 🛑 Important: This is only used for the bare-metal install 🛑 
# Update /install/start.ubuntu.sh in most cases is preferred 

echo "---------------------------------------------------------"
echo "[INSTALL] Starting NetAlertX installation for Ubuntu"
echo "---------------------------------------------------------"
echo
echo "This script will install NetAlertX on your Ubuntu system."
echo "It will clone the repository, set up necessary files, and start the application."
echo "Please ensure you have a stable internet connection."
echo "---------------------------------------------------------"

# Set environment variables
INSTALL_DIR=/app  # Specify the installation directory here

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use 'sudo'." 
    exit 1
fi

# Prepare the environment
echo "Updating packages"
echo "-----------------"
apt-get update
echo "Making sure sudo is installed"
apt-get install sudo -y

# Install Git
echo "Installing Git"
apt-get install -y git

# Clean the directory, ask for confirmation
if [ -d "$INSTALL_DIR" ]; then
  echo "The installation directory exists. Removing it to ensure a clean install."
  echo "Are you sure you want to continue? This will delete all existing files in $INSTALL_DIR."
  echo "Type:"
  echo " - 'install' to continue"
  echo " - 'update' to just update from GIT"
  echo " - 'start' to do nothing, leave install as-is"
  if [ "$1" == "install" ] || [ "$1" == "update" ] || [ "$1" == "start" ]; then
    confirmation=$1
  else
    read -p "Enter your choice: " confirmation
  fi
  if [ "$confirmation" == "install" ]; then
    # Ensure INSTALL_DIR is safe to wipe
    if [ -n "$INSTALL_DIR" ] && [ "$INSTALL_DIR" != "" ] && [ "$INSTALL_DIR" != "/" ] && [ "$INSTALL_DIR" != "." ] && [ -d "$INSTALL_DIR" ]; then
      echo "Removing existing installation..."

      # Stop nginx if running
      if command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service | grep -q nginx; then
      systemctl stop nginx 2>/dev/null
      elif command -v service >/dev/null 2>&1; then
      service nginx stop 2>/dev/null
      fi

      # Kill running NetAlertX server processes in this INSTALL_DIR
      pkill -f "python.*${INSTALL_DIR}/server" 2>/dev/null

      # Unmount only if mountpoints exist
      mountpoint -q "$INSTALL_DIR/api" && umount "$INSTALL_DIR/api" 2>/dev/null
      mountpoint -q "$INSTALL_DIR/front" && umount "$INSTALL_DIR/front" 2>/dev/null

      # Remove all contents safely
      rm -rf -- "$INSTALL_DIR"/* "$INSTALL_DIR"/.[!.]* "$INSTALL_DIR"/..?* 2>/dev/null

      # Re-clone repository
      git clone https://github.com/jokob-sk/NetAlertX "$INSTALL_DIR/"
    else
      echo "INSTALL_DIR is not set, is root, or is invalid. Aborting for safety."
      exit 1
    fi
    else
      echo "INSTALL_DIR is not set or is root. Aborting for safety."
      exit 1
    fi
  elif [ "$confirmation" == "update" ]; then
    echo "Updating the existing installation..."
    service nginx stop 2>/dev/null
   pkill -f "python ${INSTALL_DIR}/server" 2>/dev/null
    cd "$INSTALL_DIR" || { echo "Failed to change directory to $INSTALL_DIR"; exit 1; }
    git pull
  elif [ "$confirmation" == "start" ]; then
    echo "Continuing without changes."
  else
    echo "Installation aborted."
    exit 1
  fi
else
  git clone https://github.com/jokob-sk/NetAlertX "$INSTALL_DIR/"
fi

# Check for buildtimestamp.txt existence, otherwise create it
if [ ! -f "$INSTALL_DIR/front/buildtimestamp.txt" ]; then
  date +%s > "$INSTALL_DIR/front/buildtimestamp.txt"
fi

# Start NetAlertX

# This is where we setup the virtual environment and install dependencies
cd "$INSTALL_DIR/install/ubuntu" || { echo "Failed to change directory to $INSTALL_DIR/install/ubuntu"; exit 1; }
"$INSTALL_DIR/install/ubuntu/start.ubuntu.sh"
