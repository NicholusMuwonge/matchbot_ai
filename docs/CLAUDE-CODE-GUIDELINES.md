# Claude Code Guidelines

This document outlines the comprehensive guidelines that Claude must follow when writing code for the MatchBot AI project.

## 1. Project Requirements Planning (PRP)

### When to Create a PRP
- **ALWAYS** create a PRP document for any task that involves:
  - Adding new features or significant functionality
  - Infrastructure changes (Docker, databases, services)
  - Architecture modifications
  - Integration of external services
- Place PRP documents in `/docs/prps/` with naming: `{TICKET-ID}-{brief-description}.md`

### PRP Structure Requirements
1. **Overview** - Clear problem statement and solution approach
2. **Requirements** - Functional and non-functional requirements
3. **Technical Architecture** - System diagrams, component descriptions
4. **Implementation Plan** - Phased approach with clear tasks
5. **Testing Strategy** - Unit, integration, and manual testing plans
6. **Monitoring & Debugging** - Comprehensive debugging strategies
7. **Technical Decision Rationale** - Why specific choices were made
8. **Production Readiness Checklist** - Deployment considerations
9. **Risk Assessment** - Potential issues and mitigation strategies
10. **External Source References** - Potential documentation to reference with

## 2. Task Management

### TodoWrite Tool Usage
- **MANDATORY** for any multi-step task (3+ steps)
- **MANDATORY** for complex implementations requiring planning
- Update status in real-time: `pending` → `in_progress` → `completed`
- Only ONE task should be `in_progress` at any time
- Mark tasks completed IMMEDIATELY after finishing
- Add new tasks if discovered during implementation

### Task Status Rules
- `pending`: Task not yet started
- `in_progress`: Currently working on (limit to ONE)
- `completed`: Task finished successfully

### When NOT to Use TodoWrite
- Single, trivial operations (< 3 steps)
- Pure informational requests
- Simple file reads or explanations

## 3. Code Quality Standards

### General Principles
1. **Security First**: Never expose secrets, keys, or sensitive data
2. **Follow Existing Patterns**: Mimic established code conventions
3. **No Comments**: Only add comments for complex logic or business rules - code should be self-documenting
4. **Meaningful Names**: Use descriptive variable and function names - NO single letters or abbreviations (e.g., `redis_client` not `r`)
5. **Readable Over Clever**: Simple, clear code over short, complex code - prioritize maintainability
6. **Design Patterns**: Follow SOLID principles and common patterns (Factory, Singleton, Strategy)
7. **Ask for Context**: If feature requirements are unclear or lacking, ask for more details before implementation
8. **Error Handling**: Always implement proper error handling
9. **Logging**: Add structured logging for debugging

### Design Patterns & Architecture

#### SOLID Principles - MANDATORY
1. **Single Responsibility**: Each class/function has one reason to change
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Objects should be replaceable with instances of their subtypes
4. **Interface Segregation**: Many specific interfaces better than one general
5. **Dependency Inversion**: Depend on abstractions, not concretions

#### Required Design Patterns
- **Factory Pattern**: For object creation with complex logic
- **Singleton Pattern**: For single-instance services (database connections, config)
- **Strategy Pattern**: For interchangeable algorithms/behaviors
- **Dependency Injection**: For testable, loosely coupled code
- **Repository Pattern**: For data access abstraction

#### Code Quality Rules
- **Function Decomposition**: Break functions into smaller functions with very clear, descriptive names
- **Length vs Clarity**: Function name length doesn't matter - prioritize clear, concise naming over brevity
- **No Cryptic Variables**: `user_repository` not `repo`, `redis_client` not `r`
- **Self-Documenting**: Code should explain itself without comments
- **Single Level of Abstraction**: Each function should operate at one abstraction level
- **Early Returns**: Use guard clauses to reduce nesting
- **Try-Catch Mandatory**: Use proper exception handling with try-catch blocks
- **Proper Logging**: Add structured logging at appropriate levels for debugging

#### Examples of Good vs Bad Code

**❌ Bad - Complex, unclear, no error handling:**
```python
def process(r, u, d):  # What are r, u, d?
    if r and u:
        for x in d:  # What is x?
            if x.get('type') == 'premium' and x.get('status') == 'active':
                r.set(f"u:{u}:{x['id']}", json.dumps(x), ex=3600)
```

**✅ Good - Clear, decomposed, with error handling:**
```python
import logging
from typing import List, Dict
from redis import Redis

logger = logging.getLogger(__name__)

def cache_user_premium_subscriptions(
    redis_client: Redis, 
    user_id: str, 
    subscriptions: List[Dict]
) -> None:
    """Cache active premium subscriptions for a user."""
    try:
        if not _validate_cache_prerequisites(redis_client, user_id):
            return
        
        active_premium_subscriptions = _filter_active_premium_subscriptions(subscriptions)
        _store_subscriptions_in_cache(redis_client, user_id, active_premium_subscriptions)
        
        logger.info(f"Successfully cached {len(active_premium_subscriptions)} subscriptions for user {user_id}")
        
    except Exception as cache_error:
        logger.error(f"Failed to cache subscriptions for user {user_id}: {cache_error}", exc_info=True)
        raise

def _validate_cache_prerequisites(redis_client: Redis, user_id: str) -> bool:
    """Validate that we have the necessary components for caching."""
    if not redis_client:
        logger.warning("Redis client is not available")
        return False
    
    if not user_id:
        logger.warning("User ID is required for caching")
        return False
    
    return True

def _filter_active_premium_subscriptions(subscriptions: List[Dict]) -> List[Dict]:
    """Filter subscriptions to only include active premium ones."""
    return [
        subscription for subscription in subscriptions
        if _is_active_premium_subscription(subscription)
    ]

def _is_active_premium_subscription(subscription: Dict) -> bool:
    """Check if a subscription is both premium and active."""
    return (
        subscription.get('type') == 'premium' 
        and subscription.get('status') == 'active'
    )

def _store_subscriptions_in_cache(
    redis_client: Redis, 
    user_id: str, 
    subscriptions: List[Dict]
) -> None:
    """Store subscriptions in Redis cache with appropriate expiration."""
    for subscription in subscriptions:
        try:
            cache_key = _build_subscription_cache_key(user_id, subscription['id'])
            subscription_data = json.dumps(subscription)
            redis_client.set(cache_key, subscription_data, ex=3600)
            
        except KeyError as key_error:
            logger.warning(f"Subscription missing required field: {key_error}")
            continue
        except Exception as storage_error:
            logger.error(f"Failed to store subscription {subscription.get('id')}: {storage_error}")
            continue

def _build_subscription_cache_key(user_id: str, subscription_id: str) -> str:
    """Build a consistent cache key for user subscription data."""
    return f"user:{user_id}:subscription:{subscription_id}"
```

### Language-Specific Standards

#### Python/FastAPI
- Follow existing import patterns and structure
- Use type hints consistently for all parameters and return values
- Implement proper exception handling with HTTPException
- Use Pydantic models for data validation
- Follow existing routing and dependency injection patterns
- Use descriptive variable names: `database_session` not `db`, `user_repository` not `repo`
- Add comprehensive logging with appropriate levels
- **Offload Heavy Tasks**: Any task likely to cause significant overhead on the main thread MUST be executed asynchronously using Celery workers

#### Docker/Infrastructure
- **Prefer Alpine images** for size and security advantages
- Always include health checks for services
- Use named volumes for data persistence
- Implement proper service dependencies with health conditions
- Include restart policies for production readiness

#### Environment Configuration
- Add new variables to both `.env` and `.env.example`
- Use descriptive comments in `.env.example`
- Follow existing naming conventions
- Include Docker Compose and local development variants

## 4. Implementation Execution Rules

### Before Starting Implementation
1. **ASK FOR CONTEXT**: If requirements are vague, incomplete, or unclear - ASK for more details
2. **ALWAYS** read existing code to understand patterns
3. Check for existing libraries and dependencies
4. Validate the approach fits the existing architecture
5. Create PRP for complex tasks
6. Set up TodoWrite for multi-step tasks
7. **Evaluate Task Overhead**: Identify tasks that could block the main thread and plan for Celery execution

### Context Requirements - ASK IF MISSING
- **Business Logic**: What is the expected behavior?
- **Data Flow**: How should data move through the system?
- **Error Cases**: What should happen when things go wrong?
- **Performance Requirements**: Any specific performance needs?
- **Integration Points**: How does this connect with other systems?
- **Security Considerations**: Any specific security requirements?
- **User Experience**: How will users interact with this feature?
- **Task Overhead**: Will this operation take significant time or resources that could block the main thread?

### During Implementation
1. **Test incrementally** - validate each component works
2. Follow the established git workflow: `main` → `develop` → `feature_branch`
3. Use meaningful branch names: `{username}/{ticket-id}-{brief-description}`
4. Commit frequently with descriptive messages
5. Update todo status in real-time
6. **Implement Async Tasks**: Use Celery for operations that could impact main thread performance

### Error Handling Standards
- Always implement try-catch blocks for external calls
- Use appropriate HTTP status codes
- Return structured error responses
- Add proper logging for debugging
- Include retry logic where appropriate

## 5. Testing Requirements

### Testing Strategy - Focus on Major Features
- **Major Features Only**: Write comprehensive tests for significant functionality, not every small task
- **End-to-End Testing**: Full workflow testing for major features (user registration, file processing, etc.)
- **Integration Testing**: Test service-to-service communication for critical paths
- **Error Scenario Testing**: Test failure modes and recovery for major features
- **Performance Testing**: Load testing for critical user flows
- **Async Task Testing**: Validate Celery task execution and error handling for background operations

### Comprehensive Testing Requirements
- **Business Logic**: Test core business rules and edge cases
- **Data Flow**: Validate complete data processing pipelines
- **Security**: Test authentication, authorization, and input validation
- **Infrastructure**: Test service connectivity and health checks for critical services
- **User Workflows**: Test complete user journeys from start to finish

### Testing Levels
1. **Unit Tests**: For complex business logic functions and utilities
2. **Integration Tests**: For service interactions and database operations  
3. **End-to-End Tests**: For complete user workflows and major features
4. **Contract Tests**: For API interfaces and external service integrations

### Testing Tools
- Use existing testing framework (pytest for backend)
- Validate Docker Compose configurations
- Test health check endpoints for critical services
- Verify environment variable configurations
- Use realistic test data that mirrors production scenarios

## 6. Documentation Standards

### Code Documentation
- Add docstrings for all new functions and classes
- Include type hints and parameter descriptions
- Document complex logic and business rules
- Update existing documentation when modifying code

### Implementation Documentation
- Create comprehensive commit messages with implementation details
- Include architecture decisions and reasoning
- Document any deviations from original plans
- Add troubleshooting guides for complex setups

## 7. Git Workflow Standards

### Branch Management
- **NEVER** commit directly to `main` or `develop`
- Create feature branches from `develop`
- Use descriptive branch names
- Keep branches focused on single features/tasks

### Commit Standards
- Write detailed commit messages explaining the "why"
- Include implementation highlights and decisions

### Pull Request Requirements
- Target `develop` branch (not `main`)
- Include comprehensive PR description
- Add testing validation steps
- Include architecture decisions and rationale

## 8. Monitoring & Health Checks

### Mandatory Health Checks
- Every new service MUST have health check endpoints
- Include comprehensive diagnostic information
- Test connectivity to external dependencies
- Return structured JSON responses with timestamps

### Logging Standards
- Use structured logging with appropriate levels
- Include request IDs for traceability
- Add performance metrics for critical paths
- Implement log rotation for production

## 9. Production Readiness

### Deployment Considerations
- Use environment variables for configuration
- Implement proper secret management
- Add monitoring and alerting capabilities
- Include backup and recovery strategies

### Performance Standards
- Choose efficient images (Alpine over Debian)
- Implement connection pooling
- Add caching where appropriate
- Consider horizontal scaling requirements
- **Offload Heavy Operations**: Move CPU-intensive, I/O-bound, or time-consuming tasks to Celery workers to maintain API responsiveness

## 10. Architecture Decision Documentation

### Decision Recording
- Document WHY specific technologies were chosen
- Compare alternatives and explain trade-offs
- Include performance and security considerations
- Update decisions when requirements change

### Examples to Always Include
- Why Alpine vs Slim images
- Why shared backend image for Celery vs separate
- Why specific dependency versions
- Why particular service dependencies and startup order

## 11. Validation Rules

### Before Declaring Task Complete
1. **Functional Testing**: All features work as intended
2. **Integration Testing**: Services communicate properly
3. **Health Checks**: All health endpoints return success
4. **Documentation**: Implementation is properly documented
5. **Error Handling**: Failure scenarios are handled gracefully
6. **Performance**: No obvious performance bottlenecks
7. **Security**: No secrets or vulnerabilities exposed
8. **Tests**: Atleast end to end tests for each functionality if major and unit tests for complex modeules or services.

### Code Review Checklist
- [ ] **Code Quality**: Uses meaningful variable names, no single letters or abbreviations
- [ ] **Readability**: Code is simple and self-documenting, no unnecessary complexity
- [ ] **Design Patterns**: Follows SOLID principles and appropriate patterns (Factory, Strategy, etc.)
- [ ] **Context Clarity**: All requirements were clear before implementation started
- [ ] **Error Handling**: Proper exception handling with meaningful messages
- [ ] **Type Hints**: All functions have complete type annotations
- [ ] **No Comments**: Code is self-documenting (unless complex business logic)
- [ ] **Testing**: Comprehensive tests validate functionality
- [ ] **Environment Config**: Variables properly configured in both .env files
- [ ] **Health Checks**: New services have health monitoring
- [ ] **Performance**: No obvious bottlenecks or inefficiencies
- [ ] **Security**: No secrets exposed, proper input validation
- [ ] **Async Processing**: Heavy operations are properly offloaded to Celery workers

## 12. Communication Standards

### Progress Updates
- Be concise and direct in responses
- Focus on implementation highlights
- Include testing results and validation
- Mention any deviations from original plan

### Problem Reporting
- Clearly describe issues encountered
- Include steps taken to resolve
- Provide alternative approaches considered
- Ask for clarification when requirements are unclear

## 13. Continuous Improvement

### Learning from Implementation
- Document lessons learned from each task
- Update guidelines based on experience
- Share architectural decisions and reasoning
- Improve processes based on feedback

### Best Practice Evolution
- Stay current with framework best practices
- Incorporate security updates and recommendations
- Optimize for maintainability and readability
- Balance performance with code clarity

---

## Adherence Statement

**I, Claude, commit to following these guidelines consistently across all coding tasks. I will prioritize:**

1. **Clarity over Cleverness**: Simple, readable code that any developer can understand
2. **Meaningful Names**: Descriptive variables and functions, never single letters or cryptic abbreviations
3. **SOLID Principles**: Following proper design patterns and architectural principles
4. **Context First**: Asking for clarification when requirements are unclear or incomplete
5. **Self-Documenting Code**: Writing code that explains itself without comments
6. **Quality over Speed**: Taking time to write maintainable, testable code
7. **Performance-First Architecture**: Offloading heavy operations to background workers to maintain responsiveness

**These standards ensure high-quality, maintainable, secure, and well-documented code that follows industry best practices and project-specific requirements.**

**Last Updated**: 2025-08-21  
**Version**: 2.0  
**Status**: Active - Enhanced with Code Quality Focus
