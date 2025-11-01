# Mount Configuration Issues

## Issue Description

NetAlertX has detected configuration issues with your Docker volume mounts. These may include write permission problems, data loss risks, or performance concerns marked with ❌ in the table.

## Security Ramifications

Improper mount configurations can lead to data loss, performance degradation, or security vulnerabilities. For persistent data (database and configuration), using non-persistent storage like tmpfs can result in complete data loss on container restart. For temporary data, using persistent storage may unnecessarily expose sensitive logs or cache data.

## Why You're Seeing This Issue

This occurs when your Docker Compose or run configuration doesn't properly map host directories to container paths, or when the mounted volumes have incorrect permissions. The application requires specific paths to be writable for operation, and some paths should use persistent storage while others should be temporary.

## How to Correct the Issue

Review and correct your volume mounts in docker-compose.yml:

- Ensure `${NETALERTX_DB}` and `${NETALERTX_CONFIG}` use persistent host directories
- Ensure `${NETALERTX_API}`, `${NETALERTX_LOG}` have appropriate permissions
- Avoid mounting sensitive paths to non-persistent filesystems like tmpfs for critical data
- Use bind mounts with proper ownership (netalertx user: 20211:20211)

Example volume configuration:
```yaml
volumes:
  - ./data/db:/app/db
  - ./data/config:/app/config
  - ./data/log:/app/log
```

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)