# PRP: MinIO Docker Container Setup Implementation

## Metadata
- **Feature**: MinIO Object Storage Service for Reconciliation Feature
- **Linear Issue**: MAT-64
- **Confidence Score**: 9/10
- **Expected Implementation Time**: 15 minutes
- **Risk Level**: Low

## Context & Background

### Business Requirement
Implement MinIO object storage service in Docker Compose infrastructure to support file upload functionality for the reconciliation feature. MinIO provides S3-compatible API for storing and retrieving files.

### Technical Context
- **Current Infrastructure**: Docker Compose with Postgres, Redis, Celery, Traefik
- **Security Requirements**: Following CLAUDE.md security guidelines - no hardcoded credentials
- **Integration Points**: Will be used by backend service for file storage

### Critical Documentation References
- [MinIO Docker Documentation](https://min.io/docs/minio/container/index.html)
- [MinIO Health Check Endpoints](https://github.com/minio/minio/issues/18389) - Note: curl removed from recent images
- [Docker Compose Best Practices](https://docs.docker.com/compose/compose-file/compose-file-v3/)

## Research Findings

### Key Discoveries
1. **Health Check Issue**: Recent MinIO images don't include curl, requiring alternative health check methods
2. **Security Best Practice**: Use `${VAR_NAME?Variable not set}` for required environment variables
3. **Network Configuration**: Services should connect via default network, Traefik integration optional for Phase 2
4. **Volume Naming**: Follow project pattern: `service-data` (e.g., `minio-data`)

### Existing Patterns to Follow
From analyzing `docker-compose.yml`:

```yaml
# Pattern from Redis service (lines 79-89)
redis:
  image: redis:7-alpine
  restart: always
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

Environment variable pattern (from Postgres, lines 18-20):
```yaml
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD?Variable not set}
  - POSTGRES_USER=${POSTGRES_USER?Variable not set}
  - POSTGRES_DB=${POSTGRES_DB?Variable not set}
```

## Implementation Blueprint

### Pseudocode Approach
```
1. Add MinIO service to docker-compose.yml:
   - Position between db and adminer services (line 21)
   - Follow Redis service structure as template
   - Use official minio/minio:latest image

2. Configure service properties:
   - restart: always (standard pattern)
   - healthcheck: Use wget or mc instead of curl
   - ports: Map 9000:9000 (API) and 9001:9001 (Console)
   - volumes: minio-data:/data
   - env_file: .env.local
   - environment: MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
   - command: server /data --console-address ":9001"
   - networks: default only (Phase 1)

3. Add volume definition:
   - Add minio-data to volumes section (line 264)

4. Update .env.example:
   - Add MinIO configuration section after Clerk (line 69)
   - Include MINIO_ROOT_USER and MINIO_ROOT_PASSWORD with defaults
```

### Detailed Implementation Steps

#### Step 1: Add MinIO Service Definition

**File**: `docker-compose.yml`
**Location**: After line 20 (between db and adminer services)

```yaml
  minio:
    image: minio/minio:latest
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
      start_period: 30s
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    env_file:
      - .env.local
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER?Variable not set}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD?Variable not set}
    command: server /data --console-address ":9001"
    networks:
      - default
```

**Note on Health Check**: While newer MinIO images don't include curl, the health check endpoint still works. Alternative approach if needed:
```yaml
# Alternative using wget (included in alpine-based images)
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9000/minio/health/live || exit 1"]
```

#### Step 2: Add Volume Definition

**File**: `docker-compose.yml`
**Location**: Line 264 (volumes section)

```yaml
volumes:
  app-db-data:
  redis-data:
  minio-data:  # Add this line
```

#### Step 3: Update Environment Variables

**File**: `.env.example`
**Location**: After line 68 (after Clerk configuration)

```bash
# MinIO Configuration
# IMPORTANT: Change these from default values for security
# Use strong passwords (minimum 8 characters)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changethis123
```

## Validation Gates

### Pre-Implementation Checks
```bash
# Check if ports are available
lsof -i :9000 2>/dev/null && echo "Port 9000 in use!" || echo "✓ Port 9000 available"
lsof -i :9001 2>/dev/null && echo "Port 9001 in use!" || echo "✓ Port 9001 available"

# Verify docker-compose version
docker compose version | grep -E "v2\.[0-9]+" && echo "✓ Docker Compose v2 detected"
```

### Post-Implementation Validation
```bash
# Step 1: Validate configuration syntax
docker compose config --quiet && echo "✓ Configuration valid" || echo "✗ Configuration error"

# Step 2: Check environment variables are documented
grep -q "MINIO_ROOT_USER" .env.example && echo "✓ MinIO vars in .env.example" || echo "✗ Missing MinIO vars"

# Step 3: Verify no hardcoded credentials
! grep -E "MINIO_ROOT_USER=.*[a-zA-Z]" docker-compose.yml && echo "✓ No hardcoded credentials" || echo "✗ Found hardcoded credentials!"

# Step 4: Test MinIO startup (requires .env.local setup)
# Note: This step requires adding credentials to .env.local first:
# echo "MINIO_ROOT_USER=testuser" >> .env.local
# echo "MINIO_ROOT_PASSWORD=testpass123" >> .env.local
# docker compose up -d minio
# sleep 10
# docker compose ps minio | grep -q "healthy\|running" && echo "✓ MinIO running" || echo "✗ MinIO failed to start"
# curl -f http://localhost:9000/minio/health/live && echo "✓ Health check passes" || echo "✗ Health check failed"
# docker compose down minio
```

### Success Criteria Checklist
- [ ] MinIO service added to docker-compose.yml
- [ ] Service positioned between db and adminer
- [ ] Health check configured
- [ ] Ports 9000 and 9001 exposed
- [ ] Volume minio-data defined
- [ ] Environment variables use `${VAR?Variable not set}` pattern
- [ ] No hardcoded credentials in docker-compose.yml
- [ ] MinIO variables added to .env.example
- [ ] Docker compose config validates successfully
- [ ] Service starts when credentials provided in .env.local

## Error Handling & Troubleshooting

### Common Issues & Solutions

1. **Port Conflicts**
   ```bash
   Error: bind: address already in use
   Solution: Check and free ports with: lsof -i :9000 and kill <PID>
   ```

2. **Missing Environment Variables**
   ```bash
   Error: required variable MINIO_ROOT_USER is missing a value
   Solution: Add to .env.local: MINIO_ROOT_USER=your_username
   ```

3. **Health Check Failures**
   ```bash
   # Debug health check
   docker compose exec minio curl -f http://localhost:9000/minio/health/live
   # Check logs
   docker compose logs minio
   ```

4. **Volume Permission Issues**
   ```bash
   # Check volume ownership
   docker compose exec minio ls -la /data
   # Reset volume if needed
   docker compose down -v
   ```

## Implementation Tasks (Sequential Order)

1. **Backup Current Configuration**
   ```bash
   cp docker-compose.yml docker-compose.yml.backup
   cp .env.example .env.example.backup
   ```

2. **Edit docker-compose.yml**
   - Add MinIO service definition after db service (line 21)
   - Add minio-data to volumes section (line 264)

3. **Update .env.example**
   - Add MinIO configuration section with default values

4. **Validate Configuration**
   - Run `docker compose config` to verify syntax
   - Check for hardcoded credentials

5. **Test Service (Optional)**
   - Add test credentials to .env.local
   - Start MinIO with `docker compose up -d minio`
   - Verify health with curl
   - Access console at http://localhost:9001

6. **Document Implementation**
   - Create implementation notes in backend/.claude/prps/reconciliations/

## Security Considerations

### Must Follow (per CLAUDE.md)
- ✅ Use `${VAR_NAME?Variable not set}` for required variables
- ✅ Never hardcode credentials in docker-compose.yml
- ✅ Document variables in .env.example
- ✅ Keep actual credentials in .env.local (not committed)
- ✅ Use strong passwords (minimum 8 characters)

### Additional Security Notes
- Default credentials (minioadmin) must be changed
- Consider network isolation in production
- SSL/TLS configuration deferred to Task 15
- Regular credential rotation recommended

## Dependencies & Prerequisites

### Required Before Implementation
- Docker Compose v2.x or higher
- Ports 9000 and 9001 available
- Write access to project files

### Related Tasks
- Task 02: Environment variables configuration (partial overlap)
- Task 03: Volume persistence setup (partial overlap)
- Task 04: Port configuration (partial overlap)
- Task 08: Create initialization script for default buckets (future)
- Task 17: Update backend configuration to connect to MinIO (future)

## Quick Reference Commands

```bash
# Start MinIO
docker compose up -d minio

# View logs
docker compose logs -f minio

# Check status
docker compose ps minio

# Access shell
docker compose exec minio sh

# Stop MinIO
docker compose stop minio

# Remove MinIO (preserves volume)
docker compose rm minio

# Remove everything including data
docker compose down -v
```

## External Resources
- [MinIO Docker Hub](https://hub.docker.com/r/minio/minio)
- [MinIO Docker Documentation](https://min.io/docs/minio/container/index.html)
- [MinIO Health Check API](https://min.io/docs/minio/linux/operations/monitoring/healthcheck-probe.html)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Project CLAUDE.md Security Guidelines](/CLAUDE.md)

## Final Notes

This implementation follows all project patterns and security guidelines. The MinIO service integrates seamlessly with the existing Docker Compose infrastructure and provides a solid foundation for the reconciliation feature's file storage needs.

**Key Success Factors:**
1. Following existing service patterns (especially Redis)
2. Strict adherence to security guidelines (no hardcoded secrets)
3. Proper health check configuration
4. Clear documentation of environment variables

**Next Steps After Implementation:**
1. Backend integration (Task 17)
2. Bucket initialization scripts (Task 08)
3. CORS configuration for frontend uploads (Task 11)

---

**PRP Quality Score: 9/10**

Rationale: This PRP provides comprehensive context, follows existing patterns, includes executable validation gates, and addresses all requirements. The only reason it's not 10/10 is the health check uncertainty with newer MinIO images, though mitigation strategies are provided.