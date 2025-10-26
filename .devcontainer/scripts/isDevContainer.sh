#!/bin/bash
if [ ! -d /workspaces/NetAlertX/.devcontainer ]; then 
    echo ---------------------------------------------------
    echo "This script may only be run inside a devcontainer."
    echo "Not in a devcontainer, exiting..."
    echo ---------------------------------------------------
    exit 255
fi
