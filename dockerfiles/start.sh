#!/bin/bash

# This script is now mostly handled by the Dockerfile
# Only runtime cleanup remains

# Remove this script since all setup is now done at build time
rm -f $0
