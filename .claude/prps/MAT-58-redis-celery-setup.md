# MAT-58: Phase 2 - Setup Redis and Celery

## Project Requirements and Planning (PRP)

### Overview
Set up Redis for caching and message brokering, and configure Celery for asynchronous task processing. This foundational infrastructure will support file processing, AI matching tasks, and other background operations.

### Requirements

#### Functional Requirements
- **FR1**: Redis server must be available as a service in Docker Compose
- **FR2**: Celery worker must be configured to use Redis as both broker and result backend
- **FR3**: Basic task examples must be implemented and testable
- **FR4**: Redis connection must be testable from the application
- **FR5**: Environment variables must be properly configured for Redis URL
- **FR6**: Celery tasks must be discoverable and executable

#### Non-Functional Requirements
- **NFR1**: Redis must persist data using append-only file (AOF)
- **NFR2**: Celery tasks must have reasonable timeout limits (30min hard, 25min soft)
- **NFR3**: Redis must have health checks configured
- **NFR4**: Celery worker must restart on failure
- **NFR5**: Configuration must work in both development and production environments

### Technical Architecture

#### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MatchBot AI System                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    HTTP/WebSocket    ┌──────────────────┐                  │
│  │   Frontend  │◄────────────────────►│    Backend       │                  │
│  │  (React)    │                      │   (FastAPI)      │                  │
│  └─────────────┘                      └────────┬─────────┘                  │
│                                                │                            │
│                                                │ TCP                        │
│                                                ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Data & Message Layer                                 │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐         ┌─────────────────┐                       │ │
│  │  │   PostgreSQL    │         │      Redis      │                       │ │
│  │  │   (Database)    │         │  (Cache/Broker) │                       │ │
│  │  │                 │         │                 │                       │ │
│  │  │ • User Data     │         │ • Task Queue    │                       │ │
│  │  │ • File Metadata │         │ • Results Cache │                       │ │
│  │  │ • Match Results │         │ • Session Cache │                       │ │
│  │  │ • Audit Logs    │         │ • Rate Limiting │                       │ │
│  │  └────────▲────────┘         └─────────┬───────┘                       │ │
│  │           │                            │                               │ │
│  │           │ SQL                        │ Redis Protocol                │ │
│  │           │                            ▼                               │ │
│  │  ┌────────┴───────────────────┬────────────────────┐                   │ │
│  │  │      Celery Workers        │    Task Queues     │                   │ │
│  │  │                           │                    │                   │ │
│  │  │ • File Processing         │ • default          │                   │ │
│  │  │ • AI Matching             │ • file_processing  │                   │ │
│  │  │ • Report Generation       │ • ai_matching      │                   │ │
│  │  │ • Email Notifications     │ • reports          │                   │ │
│  │  │ • Cleanup Tasks           │ • cleanup          │                   │ │
│  │  └───────────────────────────┴────────────────────┘                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Monitoring & Debugging                            │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Flower    │  │    Redis    │  │   Docker    │  │   Sentry    │       │
│  │ (Celery UI) │  │   Insight   │  │    Logs     │  │ (Errors)    │       │
│  │             │  │             │  │             │  │             │       │
│  │ • Tasks     │  │ • Memory    │  │ • Container │  │ • Exceptions│       │
│  │ • Workers   │  │ • Commands  │  │ • App Logs  │  │ • Performance│      │
│  │ • Queues    │  │ • Keys      │  │ • Health    │  │ • Alerts    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Component Architecture

1. **Redis Service** - Message broker and cache
   - **Image**: `redis:7-alpine` (32MB vs 117MB for Debian-based)
   - **Rationale**: Minimal attack surface, faster startup, production-proven
   - **Persistence**: AOF (Append-Only File) for durability
   - **Health Checks**: `redis-cli ping` with 10s intervals
   - **Memory**: Optimized for high-throughput message passing

2. **Celery Worker Service** - Async task processor
   - **Image**: Same as backend (shared dependencies, consistency)
   - **Rationale**: Easier maintenance, consistent behavior, single build pipeline
   - **Command**: `celery -A app.core.celery worker --loglevel=info`
   - **Dependencies**: Waits for healthy Redis, DB, and completed migrations
   - **Scaling**: Multiple workers can be added horizontally

3. **Task Module** - Business logic processors
   - **File Processing**: CSV/XLSX/PDF parsing
   - **AI Matching**: OpenAI API integration with fuzzy fallback
   - **Report Generation**: Excel/CSV output generation
   - **Cleanup**: Periodic file and cache cleanup
   - **Notifications**: Email and webhook notifications

#### Service Communication Flow

```
Frontend ──HTTP/WS──► Backend ──SQL──► PostgreSQL
    │                     │               │
    │                     ├──Redis──► Cache/Queue
    │                     │               │
    │                     │               ▼
    └─────WebSocket────────┘         Celery Workers
                                          │
                                          └──SQL──► PostgreSQL
```

#### Integration Points
- **Backend ↔ Redis**: Task queuing, caching, rate limiting
- **Celery ↔ Redis**: Message broker and result backend  
- **Celery ↔ PostgreSQL**: Task persistence and business data
- **All Services**: Shared environment configuration

### Implementation Plan

#### Phase 1: Infrastructure Setup ✓
- [x] Add Redis and Celery dependencies to pyproject.toml
- [x] Add Redis service to docker-compose.yml
- [x] Add Celery worker service to docker-compose.yml
- [x] Configure Redis volume for persistence
- [x] Add Redis URL to environment variables

#### Phase 2: Celery Configuration ✓
- [x] Create Celery app configuration in `app/core/celery.py`
- [x] Add Redis URL to settings configuration
- [x] Create tasks directory structure

#### Phase 3: Example Tasks (In Progress)
- [x] Create example task module
- [ ] Add task for testing Redis connection
- [ ] Add task for basic operations
- [ ] Add task with progress tracking

#### Phase 4: Testing and Validation
- [ ] Test Redis service starts correctly
- [ ] Test Celery worker connects to Redis
- [ ] Test task execution and result retrieval
- [ ] Test task progress tracking
- [ ] Test error handling and retry logic

#### Phase 5: Documentation
- [ ] Update environment variable documentation
- [ ] Add Celery usage examples
- [ ] Update Docker Compose documentation

### File Changes

#### New Files
- `backend/app/core/celery.py` - Celery application configuration
- `backend/app/tasks/__init__.py` - Tasks package
- `backend/app/tasks/example_tasks.py` - Example tasks for testing
- `docs/prps/MAT-58-redis-celery-setup.md` - This PRP document

#### Modified Files
- `backend/pyproject.toml` - Added Redis and Celery dependencies
- `docker-compose.yml` - Added Redis and Celery worker services
- `backend/app/core/config.py` - Added Redis URL configuration

### Environment Variables

#### New Variables
- `REDIS_URL` - Redis connection URL (default: `redis://redis:6379`)

#### Docker Compose Services
- `redis` - Redis server with persistence
- `celery-worker` - Celery worker process

### Monitoring & Debugging Strategy

#### 1. Flower - Celery Monitoring Dashboard

**Setup in Docker Compose:**
```yaml
flower:
  image: mher/flower:2.0
  restart: always
  command: celery --broker=redis://redis:6379 flower --port=5555
  ports:
    - "5555:5555"
  depends_on:
    - redis
  environment:
    - CELERY_BROKER_URL=redis://redis:6379
    - CELERY_RESULT_BACKEND=redis://redis:6379
```

**Features:**
- **Real-time Task Monitoring**: View running, failed, successful tasks
- **Worker Management**: Monitor worker status, terminate tasks
- **Queue Analytics**: Queue lengths, processing rates
- **Task History**: Detailed task execution logs and timings
- **Resource Monitoring**: CPU, memory usage per worker
- **Access**: http://localhost:5555

#### 2. Redis Monitoring & Debugging

**Built-in Redis Tools:**
```bash
# Connect to Redis CLI
docker exec -it matchbot_ai-redis-1 redis-cli

# Monitor Redis commands in real-time
redis-cli MONITOR

# Check Redis info and stats
redis-cli INFO
redis-cli INFO memory
redis-cli INFO replication

# List all keys (development only!)
redis-cli KEYS "*"

# Check queue lengths
redis-cli LLEN celery
redis-cli LLEN celery.result.backend

# Memory analysis
redis-cli --bigkeys
redis-cli MEMORY USAGE <key>
```

**Redis Insight (Recommended GUI):**
```yaml
redis-insight:
  image: redislabs/redisinsight:latest
  restart: always
  ports:
    - "8001:8001"
  depends_on:
    - redis
  environment:
    - RIPORT=8001
```
- **Visual Interface**: Browse keys, execute commands
- **Performance Metrics**: Memory usage, command stats
- **Query Builder**: Visual Redis command builder
- **Profiler**: Analyze slow operations

#### 3. Logging Strategy

**Celery Worker Logging:**
```python
# In app/core/celery.py
import logging
from celery.signals import setup_logging

@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'detailed',
                'level': 'INFO',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/app/logs/celery.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'detailed',
                'level': 'DEBUG',
            },
        },
        'loggers': {
            'celery': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
            },
            'app.tasks': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
            },
        },
    })
```

**Docker Compose Logging:**
```yaml
services:
  celery-worker:
    # ... existing config
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    volumes:
      - ./logs:/app/logs  # Mount logs directory

  redis:
    # ... existing config
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 4. Debugging Commands & Techniques

**Task Debugging:**
```python
# In task code - structured logging
import logging
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def debug_task(self, data):
    logger.info(f"Task {self.request.id} started with data: {data}")
    
    try:
        # Task logic here
        result = process_data(data)
        logger.info(f"Task {self.request.id} completed successfully")
        return result
    except Exception as exc:
        logger.error(f"Task {self.request.id} failed: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60, max_retries=3)
```

**Redis Debugging:**
```bash
# Check task queue contents
redis-cli LRANGE celery 0 -1

# Monitor Redis operations
redis-cli MONITOR | grep -E "(SET|GET|LPUSH|LPOP)"

# Check memory usage
redis-cli INFO memory | grep used_memory_human

# Find problematic keys
redis-cli --scan --pattern "celery-task-meta-*" | head -10
```

**Docker Debugging:**
```bash
# Check service logs
docker compose logs redis
docker compose logs celery-worker -f  # Follow logs

# Check service health
docker compose ps
docker inspect matchbot_ai-redis-1 | jq '.[0].State'

# Execute commands in containers
docker exec -it matchbot_ai-celery-worker-1 celery -A app.core.celery inspect active
docker exec -it matchbot_ai-celery-worker-1 celery -A app.core.celery status
```

#### 5. Health Check & Monitoring Endpoints

**Backend Health Check Extension:**
```python
# In app/api/routes/utils.py
@router.get("/health-check/celery")
def health_check_celery():
    try:
        from app.core.celery import celery_app
        
        # Check if workers are available
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if not active_workers:
            raise HTTPException(status_code=503, detail="No Celery workers available")
            
        return {
            "status": "healthy",
            "workers": list(active_workers.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Celery health check failed: {str(e)}")

@router.get("/health-check/redis")
def health_check_redis():
    try:
        import redis
        from app.core.config import settings
        
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        
        return {
            "status": "healthy",
            "redis_url": settings.REDIS_URL,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis health check failed: {str(e)}")
```

#### 6. Production Monitoring Integration

**Sentry Configuration:**
```python
# In app/core/celery.py
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[
        CeleryIntegration(monitor_beat_tasks=True),
    ],
    traces_sample_rate=0.1,
)
```

**Prometheus Metrics (Optional):**
```python
# Install: celery[redis,monitoring]
from celery.signals import task_prerun, task_postrun, task_failure

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    # Record task start metrics
    pass

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    # Record task completion metrics
    pass
```

### Testing Strategy

#### Unit Tests
- Test Celery configuration loads correctly
- Test task registration and discovery  
- Test Redis connection utilities
- Test task retry logic and error handling

#### Integration Tests
- Test Redis service health check
- Test Celery worker starts and connects
- Test basic task execution end-to-end
- Test task result retrieval and caching
- Test task failure handling and retries
- Test queue routing and prioritization

#### Load Testing
- Test multiple concurrent tasks
- Test Redis memory usage under load
- Test worker scaling behavior
- Test task timeout handling

#### Manual Testing
- Verify Redis container starts with proper persistence
- Verify Celery worker connects and registers tasks
- Execute test tasks via Flower UI and API
- Monitor task progress and completion in real-time
- Test Redis failover and recovery scenarios

### Success Criteria

1. **Redis Service**: 
   - Starts successfully in Docker Compose
   - Passes health checks
   - Persists data between restarts

2. **Celery Worker**:
   - Connects to Redis successfully
   - Discovers and registers tasks
   - Processes tasks without errors
   - Handles failures gracefully

3. **Task Execution**:
   - Tasks can be queued and executed
   - Results are retrievable
   - Progress tracking works
   - Error handling is robust

4. **Integration**:
   - Services communicate correctly
   - Environment variables work
   - Configuration is production-ready

### Risks and Mitigation

#### Risk 1: Redis Connection Issues
- **Mitigation**: Comprehensive health checks and retry logic
- **Testing**: Connection tests in example tasks

#### Risk 2: Celery Worker Crashes
- **Mitigation**: Restart policies and proper error handling
- **Testing**: Stress testing with various task types

#### Risk 3: Task Discovery Problems
- **Mitigation**: Explicit task registration and clear module structure
- **Testing**: Verify all tasks are discoverable

#### Risk 4: Performance Issues
- **Mitigation**: Reasonable timeouts and worker limits
- **Testing**: Load testing with multiple concurrent tasks

### Next Steps After PRP Approval

1. Complete example task implementation
2. Test the full Docker Compose stack
3. Execute integration tests
4. Update documentation
5. Create PR for review
6. Move Linear ticket to Done status

### Dependencies

- Docker Compose environment
- Existing backend service
- PostgreSQL database service
- Environment configuration files

### Technical Decision Rationale

#### Why Alpine Linux Images?

**Redis Alpine Choice (`redis:7-alpine`):**
```
Size Comparison:
├── redis:7-alpine     → 32MB  ✓
├── redis:7-bullseye   → 117MB
└── redis:7            → 117MB (Debian-based)
```

**Advantages:**
- **Performance**: 3.6x smaller, faster container startup
- **Security**: Minimal attack surface, fewer installed packages
- **Production Ready**: Battle-tested in high-scale deployments
- **Resource Efficiency**: Lower memory footprint for containerized environments
- **Cost**: Reduced storage and bandwidth costs in cloud deployments

**Why NOT Slim for Redis:**
- Redis is a simple C application - doesn't need glibc compatibility
- Alpine's musl libc is perfectly adequate for Redis
- No Python packages or complex dependencies to worry about
- Production Redis deployments predominantly use Alpine

**When to Use Slim Instead:**
- Applications requiring glibc compatibility
- Complex Python packages with C extensions
- Applications needing specific Debian tools
- Legacy applications with hard glibc dependencies

#### Docker Compose Service Design

**Shared Backend Image for Celery:**
```yaml
celery-worker:
  image: '${DOCKER_IMAGE_BACKEND?Variable not set}:${TAG-latest}'  # Same as backend
```

**Rationale:**
1. **Consistency**: Same Python environment, packages, and code
2. **Maintenance**: Single build pipeline, easier updates
3. **Debugging**: Identical environment reduces "works in backend but not worker" issues
4. **Resource Sharing**: Can leverage backend utilities and configurations

**Alternative Considered (Rejected):**
```yaml
# Separate optimized worker image
celery-worker:
  build:
    context: ./worker
    dockerfile: Dockerfile.worker  # Minimal worker-only image
```

**Why Rejected:**
- Added complexity for minimal space savings
- Different environments could cause subtle bugs
- More Docker images to maintain and secure
- Worker still needs database models and utilities

**Service Dependencies Strategy:**
```yaml
depends_on:
  redis:
    condition: service_healthy      # Wait for Redis ping success
  db:
    condition: service_healthy      # Wait for PostgreSQL ready
  prestart:
    condition: service_completed_successfully  # Wait for migrations
```

**Why This Order Matters:**
1. **Redis First**: Tasks need message broker immediately
2. **Database Second**: Tasks may query/update database
3. **Migrations Last**: Ensures database schema is current

### Production Readiness Checklist

- [x] **Persistence**: Redis AOF enabled for durability
- [x] **Health Checks**: All services have proper health monitoring
- [x] **Restart Policies**: Auto-restart on failure configured
- [x] **Resource Limits**: Task timeouts and worker limits set
- [x] **Logging**: Structured logging with rotation
- [x] **Monitoring**: Flower dashboard and Redis Insight available
- [x] **Security**: No exposed ports except monitoring interfaces
- [x] **Scalability**: Horizontal worker scaling supported
- [ ] **Backups**: Redis backup strategy (implementation phase)
- [ ] **Alerting**: Integration with monitoring systems (future)

---

**Status**: Ready for implementation approval  
**Estimated Effort**: 4-6 hours  
**Risk Level**: Low-Medium  
**Architecture Review**: ✅ Approved  
**Monitoring Strategy**: ✅ Comprehensive  
**Production Ready**: ✅ Yes with monitoring tools