#!/bin/bash
echo "Initializing backend..."
# Future backend initialization steps can go here.
# For now, we'll just ensure permissions are correct.
chown -R nginx:www-data "${NETALERTX_APP}"
echo "Backend initialized."
