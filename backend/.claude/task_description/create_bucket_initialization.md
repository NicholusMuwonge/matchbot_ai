# Task Description: Create MinIO Bucket Initialization Script

## Overview
Implement automatic bucket creation for MinIO on startup to ensure required buckets exist for the reconciliation feature without manual intervention.

## Requirements

### Primary Objectives
1. **Automatic Bucket Creation**: Create required buckets on MinIO startup
2. **Service Dependencies**: Ensure initialization runs only after MinIO is healthy
3. **Idempotent Operation**: Script should be safe to run multiple times
4. **Configurable Buckets**: Easy to add/remove buckets as needed

### Required Buckets
- `reconciliation-files` - Main bucket for uploaded reconciliation files
- `temp-uploads` - Temporary storage for file processing
- `processed-files` - Storage for processed/validated files

### Technical Specifications
- **Image**: Use official `minio/mc:latest` (MinIO Client)
- **Dependencies**: Wait for MinIO service to be healthy before running
- **Network**: Connect to same network as MinIO service
- **Credentials**: Use same environment variables as MinIO service
- **Exit Strategy**: Container should exit successfully after initialization

## Implementation Approach

### Docker Compose Service
Create a new service `minio-init` that:
- Uses MinIO client image (`minio/mc`)
- Depends on MinIO service health check
- Runs initialization script and exits
- Uses environment variables for credentials

### Initialization Script Logic
1. **Wait for MinIO**: Poll until MinIO API is accessible
2. **Set Alias**: Configure mc client to connect to MinIO
3. **Create Buckets**: Create required buckets (ignore if exists)
4. **Set Policies**: Configure basic bucket policies if needed
5. **Exit Cleanly**: Exit with success status

### Error Handling
- Retry connection attempts with exponential backoff
- Log clear messages for each step
- Handle existing buckets gracefully
- Exit with error if critical failures occur

## Expected File Changes

### docker-compose.yml
Add `minio-init` service after MinIO service definition:
```yaml
minio-init:
  image: minio/mc:latest
  depends_on:
    minio:
      condition: service_healthy
  env_file:
    - .env.local
  entrypoint: >
    /bin/sh -c "
    # Initialization script here
    "
  networks:
    - default
```

### Environment Variables
No new environment variables required - reuse existing MinIO credentials:
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`

## Testing & Validation

### Pre-Implementation Tests
```bash
# Verify MinIO is running
docker compose ps minio

# Check MinIO health
curl -f http://localhost:9000/minio/health/live
```

### Post-Implementation Tests
```bash
# Start services
docker compose up -d minio minio-init

# Check initialization logs
docker compose logs minio-init

# Verify buckets were created
curl -X GET http://localhost:9000/ \
  --user testuser:testpass123

# Or use mc client directly
mc alias set local http://localhost:9000 testuser testpass123
mc ls local/
```

### Expected Output
```
reconciliation-files/
temp-uploads/
processed-files/
```

## Success Criteria
- [x] MinIO starts successfully
- [x] Initialization service waits for MinIO health check
- [x] All required buckets are created
- [x] Buckets persist after container restart
- [x] Initialization service exits cleanly
- [x] No duplicate bucket creation errors
- [x] Service can be run multiple times safely

## Security Considerations
- Use environment variables for credentials (no hardcoding)
- MinIO client connects using internal Docker network
- Bucket policies follow principle of least privilege
- No unnecessary persistent volumes for init container

## Performance Considerations
- Initialization runs once per stack startup
- Minimal resource usage (exits quickly)
- No impact on MinIO performance
- Fast startup with health check dependencies

## Maintenance & Operations

### Monitoring
- Check initialization logs: `docker compose logs minio-init`
- Verify bucket existence via MinIO console
- Monitor container exit codes

### Adding New Buckets
1. Update the initialization script with new bucket names
2. Add `mc mb --ignore-existing minio/new-bucket-name;`
3. Restart the stack to apply changes

### Troubleshooting Common Issues
1. **Init service fails**: Check MinIO health and credentials
2. **Buckets not created**: Review initialization logs
3. **Permission errors**: Verify MINIO_ROOT_USER credentials
4. **Network issues**: Ensure services on same network

## Commands for Testing

### Start Services
```bash
# Start MinIO and initialization
docker compose up -d minio minio-init

# Watch logs
docker compose logs -f minio-init
```

### Manual Bucket Verification
```bash
# Using curl
curl -u testuser:testpass123 http://localhost:9000/

# Using mc client
mc alias set local http://localhost:9000 testuser testpass123
mc ls local/
```

### Debug Commands
```bash
# Check service status
docker compose ps

# View detailed logs
docker compose logs minio-init

# Restart initialization
docker compose restart minio-init
```

## Integration Points
- **Backend Service**: Will use these buckets via MinIOService
- **File Upload API**: Will store files in appropriate buckets
- **Reconciliation Feature**: Main consumer of bucket structure
- **Frontend**: Will upload to presigned URLs for these buckets

## Future Enhancements
- Bucket lifecycle policies configuration
- Custom bucket policies per use case
- Automated bucket cleanup scripts
- Health check endpoints for bucket validation