#!/bin/sh
# ramdisk-check.sh - Verify critical paths are backed by ramdisk and warn on fallback storage.

warn_if_not_ramdisk() {
    path="$1"

    if cat /proc/mounts| grep ${path} | grep -qE 'tmpfs|ramfs'; then
        return 0
    fi

    cat >&2 <<EOF
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
  ATTENTION: ${path} is not on a ramdisk.
             Mount this folder inside the container as tmpfs or ramfs.

  NetAlertX expects this location to live in memory for fast reads and writes.
  Running it on disk will severely degrade performance for every user.

  Fix: Please mount ${path} as tmpfs/ramfs.
       eg.  --mount type=tmpfs,destination=${path}
  Restart the container after adding the ramdisk mount.
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
EOF
    exit 1
}

warn_if_not_ramdisk "${NETALERTX_API}"
warn_if_not_ramdisk "${NETALERTX_LOG}"

if [ ! -f "${SYSTEM_NGINIX_CONFIG}/conf.active" ]; then
    echo "Note: Using default listen address ${LISTEN_ADDR}:${PORT} (no ${SYSTEM_NGINIX_CONFIG}/conf.active override)."
fi
