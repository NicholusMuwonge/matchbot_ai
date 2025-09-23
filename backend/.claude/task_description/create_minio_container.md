# Task 01: Create Docker Compose Service Definition for MinIO Container

## Task Overview
**Linear Issue**: MAT-64
**Objective**: Add MinIO object storage service to the existing docker-compose.yml infrastructure for the reconciliation feature file upload functionality.

## Requirements

### 1. Docker Image Selection
- **Image**: Use official MinIO image `minio/minio:latest`
  - Alternative for production: Pin to specific version (e.g., `minio/minio:RELEASE.2024-09-22T00-33-43Z`)
- **Rationale**: Official image is well-maintained, secure, and compatible with S3 API

### 2. Service Configuration

#### Service Name
- Name: `minio`
- Must be consistent with other services in the stack

#### Container Settings
- **Restart Policy**: `always` (matches existing services pattern)
- **Health Check**: Required for container monitoring
  ```
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 20s
    retries: 3
    start_period: 30s
  ```

#### Network Configuration
- Add to existing networks:
  - `default` network for internal communication
  - Consider `traefik-public` if external access needed (Phase 2)

#### Port Mapping
- **9000**: MinIO API (S3-compatible)
- **9001**: MinIO Console (Web UI)
- Map as: `"9000:9000"` and `"9001:9001"`

#### Volume Configuration
- Data persistence: `minio-data:/data`
- Must be defined in volumes section

#### Environment Variables (Following CLAUDE.md Security Guidelines)
- **CRITICAL**: Never hardcode credentials
- Use environment variable references:
  ```
  MINIO_ROOT_USER: ${MINIO_ROOT_USER?Variable not set}
  MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD?Variable not set}
  ```
- Add to `.env.local` (not committed):
  ```
  MINIO_ROOT_USER=<secure_username>
  MINIO_ROOT_PASSWORD=<secure_password_min_8_chars>
  ```

#### Command Configuration
- Command: `server /data --console-address ":9001"`
- This starts MinIO server with data directory and console on port 9001

### 3. Integration Points

#### Dependencies
- No hard dependencies on other services
- Soft dependency: Should start before backend service

#### Service Order
- Place after `db` service
- Before `backend` service (when added)

### 4. Security Considerations (Per CLAUDE.md)

#### Environment Variables
- ✅ Use `${VAR_NAME?Variable not set}` syntax
- ✅ Never commit actual credentials
- ✅ Document required vars in `.env.example`

#### Access Control
- Default credentials MUST be changed from `minioadmin`
- Use strong passwords (minimum 8 characters)
- Consider implementing SSL/TLS in production (Task 15)

### 5. Volume Definition
Add to volumes section:
```
volumes:
  minio-data:
```

### 6. Service Placement
Insert the service definition between `db` and `adminer` services to maintain logical grouping of data storage services.

### 7. Additional Considerations

#### Development vs Production
- **Development**: Current configuration is suitable
- **Production**:
  - Use specific image version tags
  - Implement SSL/TLS (covered in Task 15)
  - Consider distributed mode for HA

#### Monitoring
- Health check endpoint ensures service availability
- Console accessible at `http://localhost:9001`

#### Data Persistence
- Volume ensures data survives container restarts
- Consider backup strategies (Task 22)

### 8. Testing Checklist
After implementation:
- [ ] Container starts without errors
- [ ] Health check passes
- [ ] API accessible on port 9000
- [ ] Console accessible on port 9001
- [ ] Environment variables properly loaded
- [ ] No hardcoded credentials in docker-compose.yml
- [ ] Volume properly mounted

### 9. Dependencies on Other Tasks
- Task 02: Environment variables configuration
- Task 03: Volume persistence setup
- Task 04: Port configuration

### 10. Edge Cases & Warnings

#### Port Conflicts
- Ensure ports 9000/9001 are not in use
- Check with: `lsof -i :9000` and `lsof -i :9001`

#### Memory Requirements
- MinIO requires minimum 1GB RAM
- Monitor with `docker stats`

#### Firewall Rules
- May need to allow ports 9000/9001 in firewall
- Development: Usually not required
- Production: Configure as needed

#### Docker Compose Version
- Requires Docker Compose v2.x or higher
- Verify with: `docker compose version`

### 11. Success Criteria
- MinIO service defined in docker-compose.yml
- No hardcoded secrets (per CLAUDE.md)
- Service starts successfully
- Health check passes
- Accessible via configured ports
- Data persists across restarts

### 12. Debugging & Logging

#### Viewing Logs
- **Real-time logs**: `docker compose logs -f minio`
- **Last 100 lines**: `docker compose logs --tail=100 minio`
- **Logs since timestamp**: `docker compose logs --since="2024-01-01T00:00:00" minio`
- **Save logs to file**: `docker compose logs minio > minio.log`

#### Debug Commands
- **Container status**: `docker compose ps minio`
- **Inspect container**: `docker inspect matchbot_ai-minio-1`
- **Container resource usage**: `docker stats minio`
- **Network inspection**: `docker compose exec minio netstat -tulpn`

#### Accessing MinIO Shell
- **Interactive shell**: `docker compose exec minio sh`
- **MinIO client (mc) commands**:
  ```bash
  # Inside container
  mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
  mc admin info local
  mc admin service status local
  ```

#### Common Debug Scenarios

**Container won't start:**
```bash
# Check if ports are in use
lsof -i :9000
lsof -i :9001

# Check Docker compose syntax
docker compose config

# Verbose startup
docker compose up minio
```

**Authentication issues:**
```bash
# Verify environment variables
docker compose exec minio env | grep MINIO

# Test credentials
curl -I http://localhost:9000
```

**Storage issues:**
```bash
# Check volume mounts
docker compose exec minio df -h
docker compose exec minio ls -la /data

# Volume inspection
docker volume inspect matchbot_ai_minio-data
```

**Health check failures:**
```bash
# Manual health check
docker compose exec minio curl -f http://localhost:9000/minio/health/live

# Check health status
docker inspect matchbot_ai-minio-1 --format='{{json .State.Health}}' | jq
```

#### Log Levels
Add to environment variables for verbose logging:
```yaml
MINIO_LOG_LEVEL: DEBUG  # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
```

#### Monitoring Endpoints
- **Health**: http://localhost:9000/minio/health/live
- **Readiness**: http://localhost:9000/minio/health/ready
- **Metrics**: http://localhost:9000/minio/v2/metrics/cluster

#### Troubleshooting Tips
1. **Always check logs first**: Most issues are evident in logs
2. **Verify network connectivity**: Ensure containers can communicate
3. **Check permissions**: MinIO needs write access to data directory
4. **Monitor resources**: Use `docker stats` to check memory/CPU
5. **Test incrementally**: Start with basic config, add features gradually

### 13. References
- [MinIO Docker Documentation](https://min.io/docs/minio/container/index.html)
- [Docker Compose Best Practices](https://docs.docker.com/compose/compose-file/compose-file-v3/)
- [MinIO Debugging Guide](https://min.io/docs/minio/linux/operations/troubleshooting.html)
- Project CLAUDE.md security guidelines
- Existing docker-compose.yml patterns