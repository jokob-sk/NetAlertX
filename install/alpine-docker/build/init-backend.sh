#!/bin/bash
echo "Initializing backend..."
# Future backend initialization steps can go here.
# For now, we'll just ensure permissions are correct.
chown -R nginx:www-data "${NETALERTX_APP}"
chmod 750 "${NETALERTX_APP}"/config "${NETALERTX_APP}"/log "${NETALERTX_APP}"/db
find "${NETALERTX_APP}"/config "${NETALERTX_APP}"/log "${NETALERTX_APP}"/db -type f -exec chmod 640 {} \;
echo "Backend initialized."
