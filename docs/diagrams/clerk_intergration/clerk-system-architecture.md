# Clerk Authentication System Architecture Diagrams

## System Overview Diagram

```mermaid
graph TB
    %% External Services
    Clerk[Clerk Authentication Service]
    Frontend[Frontend Application]
    
    %% Main Application Components
    subgraph "Backend Application"
        API[FastAPI Routes]
        ClerkService[ClerkService]
        UserSyncService[UserSyncService]
        WebhookProcessor[WebhookProcessor]
        
        %% Background Processing
        subgraph "Background Tasks"
            Celery[Celery Workers]
            Redis[(Redis Queue)]
        end
        
        %% Data Layer
        subgraph "Data Layer"
            UserModel[(User Model)]
            WebhookModel[(WebhookEvent Model)]
            DB[(PostgreSQL Database)]
        end
    end
    
    %% Connections
    Frontend -.->|Auth Requests| Clerk
    Frontend -->|API Calls| API
    Clerk -.->|Webhooks| WebhookProcessor
    
    API --> ClerkService
    API --> UserSyncService
    
    ClerkService -.->|API Calls| Clerk
    UserSyncService --> UserModel
    UserSyncService --> DB
    
    WebhookProcessor --> Redis
    WebhookProcessor --> WebhookModel
    Redis --> Celery
    Celery --> UserSyncService
    
    UserModel --> DB
    WebhookModel --> DB
    
    %% Styling
    classDef external fill:#e1f5fe
    classDef service fill:#f3e5f5
    classDef data fill:#e8f5e8
    classDef queue fill:#fff3e0
    
    class Clerk,Frontend external
    class ClerkService,UserSyncService,WebhookProcessor service
    class UserModel,WebhookModel,DB data
    class Redis,Celery queue
```

## User Registration Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Clerk
    participant Backend
    participant WebhookProcessor
    participant Celery
    participant Database
    
    User->>Frontend: Sign up
    Frontend->>Clerk: Create user account
    Clerk->>Frontend: User created (with ID)
    Frontend->>User: Registration successful
    
    Note over Clerk,Backend: Webhook Flow (Async)
    Clerk->>Backend: POST /webhooks/clerk (user.created)
    Backend->>WebhookProcessor: Process webhook
    WebhookProcessor->>WebhookProcessor: Verify signature
    WebhookProcessor->>Database: Create webhook event record
    WebhookProcessor->>Celery: Schedule user sync task
    WebhookProcessor->>Backend: Return 200 OK
    
    Note over Celery,Database: Background Processing
    Celery->>UserSyncService: Execute sync task
    UserSyncService->>Database: Create/update local user
    UserSyncService->>Database: Update webhook event status
```

## User Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Clerk
    participant Backend
    participant ClerkService
    participant Database
    
    User->>Frontend: Login
    Frontend->>Clerk: Authenticate user
    Clerk->>Frontend: Return session token
    
    User->>Frontend: Make API request
    Frontend->>Backend: API call with session token
    Backend->>ClerkService: Validate session token
    ClerkService->>Clerk: Verify token
    Clerk->>ClerkService: Token validation result
    ClerkService->>Backend: User authentication status
    
    alt Valid token
        Backend->>Database: Get/create local user
        Database->>Backend: User data
        Backend->>Frontend: API response
        Frontend->>User: Show content
    else Invalid token
        Backend->>Frontend: 401 Unauthorized
        Frontend->>User: Redirect to login
    end
```

## Webhook Processing State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending : Webhook received
    
    Pending --> Processing : Signature verified
    Pending --> Invalid : Invalid signature
    Pending --> Ignored : Unknown event type
    
    Processing --> Success : Processing completed
    Processing --> Failed : Error occurred
    
    Failed --> Processing : Retry (if attempts < max)
    Failed --> Failed : Max retries reached
    
    Success --> [*]
    Invalid --> [*] 
    Ignored --> [*]
    Failed --> [*] : After max retries
    
    note right of Processing
        Background task
        scheduled via Celery
    end note
    
    note right of Failed
        Exponential backoff:
        2^retry_count minutes
        (max 60 minutes)
    end note
```

## User Synchronization Process

```mermaid
flowchart TD
    Start([Webhook Event Received]) --> ValidateSig{Validate Signature}
    ValidateSig -->|Invalid| InvalidSig[Mark as Invalid]
    ValidateSig -->|Valid| CheckType{Check Event Type}
    
    CheckType -->|user.created| CreateTask[Schedule Create Task]
    CheckType -->|user.updated| UpdateTask[Schedule Update Task] 
    CheckType -->|user.deleted| DeleteTask[Schedule Delete Task]
    CheckType -->|other| IgnoreEvent[Mark as Ignored]
    
    CreateTask --> CeleryQueue[Add to Celery Queue]
    UpdateTask --> CeleryQueue
    DeleteTask --> CeleryQueue
    
    CeleryQueue --> ProcessTask[Celery Worker Processes Task]
    
    ProcessTask --> CheckUser{User Exists Locally?}
    
    CheckUser -->|Yes| UpdateLocal[Update Local User]
    CheckUser -->|No| CreateLocal[Create Local User]
    
    UpdateLocal --> CheckConflict{Email Conflict?}
    CreateLocal --> CheckConflict
    
    CheckConflict -->|Yes| ResolveConflict[Resolve Conflict]
    CheckConflict -->|No| SaveUser[Save User to DB]
    
    ResolveConflict --> SaveUser
    SaveUser --> UpdateWebhook[Mark Webhook as Success]
    
    ProcessTask -->|Error| RetryTask{Retry Count < Max?}
    RetryTask -->|Yes| ScheduleRetry[Schedule Retry with Backoff]
    RetryTask -->|No| MarkFailed[Mark as Failed]
    
    ScheduleRetry --> CeleryQueue
    
    InvalidSig --> End([End])
    IgnoreEvent --> End
    UpdateWebhook --> End
    MarkFailed --> End
```

## Database Schema Relationships

```mermaid
erDiagram
    USER {
        uuid id PK
        string email UK
        string clerk_user_id UK "Nullable"
        string auth_provider "local|clerk"
        boolean is_synced
        boolean email_verified
        string first_name "Nullable"
        string last_name "Nullable"
        string full_name "Nullable"
        string profile_image_url "Nullable"
        datetime created_at
        datetime last_login "Nullable"
        string hashed_password
        boolean is_active
        boolean is_superuser
    }
    
    WEBHOOK_EVENT {
        int id PK
        string webhook_id UK
        string event_type
        enum status "pending|processing|success|failed|invalid|ignored"
        datetime processed_at "Nullable"
        int retry_count
        int max_retries
        datetime next_retry_at "Nullable"
        string error_message "Nullable"
        json error_details "Nullable"
        json raw_data
        json processed_data "Nullable"
        string source_ip "Nullable"
        string user_agent "Nullable"
        datetime created_at
        datetime updated_at "Nullable"
    }
    
    ITEM {
        uuid id PK
        uuid owner_id FK
        string title
        string description "Nullable"
    }
    
    USER ||--o{ ITEM : owns
    USER ||--o{ WEBHOOK_EVENT : "processed_for"
```

## Service Layer Architecture

```mermaid
graph TB
    subgraph "API Layer"
        UserRoutes[User Routes]
        AuthRoutes[Auth Routes]
        WebhookRoutes[Webhook Routes]
    end
    
    subgraph "Service Layer"
        ClerkService[ClerkService]
        UserSyncService[UserSyncService]
        
        subgraph "Utility Services"
            ClerkJWTValidator[JWT Validator]
            ClerkUserService[User Service]
            AsyncClerkService[Async Wrapper]
        end
    end
    
    subgraph "Processing Layer" 
        WebhookProcessor[Webhook Processor]
        
        subgraph "Background Tasks"
            SyncUserTask[Sync User Task]
            FetchUserTask[Fetch User Task]
            DeleteUserTask[Delete User Task]
            StatsTask[Stats Task]
        end
    end
    
    subgraph "Data Access Layer"
        UserCRUD[User CRUD]
        WebhookCRUD[Webhook CRUD]
        Database[(Database)]
    end
    
    %% API to Service connections
    UserRoutes --> ClerkService
    UserRoutes --> UserSyncService
    AuthRoutes --> ClerkJWTValidator
    WebhookRoutes --> WebhookProcessor
    
    %% Service layer connections
    ClerkJWTValidator --> AsyncClerkService
    ClerkUserService --> AsyncClerkService
    AsyncClerkService --> ClerkService
    
    %% Processing connections
    WebhookProcessor --> SyncUserTask
    WebhookProcessor --> FetchUserTask
    WebhookProcessor --> DeleteUserTask
    
    SyncUserTask --> UserSyncService
    FetchUserTask --> UserSyncService
    DeleteUserTask --> UserSyncService
    StatsTask --> UserSyncService
    
    %% Data access
    UserSyncService --> UserCRUD
    WebhookProcessor --> WebhookCRUD
    UserCRUD --> Database
    WebhookCRUD --> Database
    
    %% External connections
    ClerkService -.->|HTTP API| Clerk[Clerk API]
    
    %% Styling
    classDef api fill:#e3f2fd
    classDef service fill:#f3e5f5
    classDef processing fill:#fff3e0
    classDef data fill:#e8f5e8
    classDef external fill:#ffebee
    
    class UserRoutes,AuthRoutes,WebhookRoutes api
    class ClerkService,UserSyncService,ClerkJWTValidator,ClerkUserService,AsyncClerkService service
    class WebhookProcessor,SyncUserTask,FetchUserTask,DeleteUserTask,StatsTask processing
    class UserCRUD,WebhookCRUD,Database data
    class Clerk external
```

## Error Handling and Retry Logic

```mermaid
graph TD
    TaskStart([Task Execution Starts]) --> TryExecute[Execute Task]
    
    TryExecute --> Success{Success?}
    Success -->|Yes| TaskComplete[Mark as Success]
    Success -->|No| CheckError{Error Type?}
    
    CheckError -->|ClerkError| IsRetryable{Retryable?}
    CheckError -->|NetworkError| IsRetryable
    CheckError -->|UserSyncError| IsRetryable
    CheckError -->|ValidationError| NotRetryable[Mark as Failed]
    CheckError -->|UnknownError| NotRetryable
    
    IsRetryable -->|Yes| CheckRetryCount{Retry Count < Max?}
    IsRetryable -->|No| NotRetryable
    
    CheckRetryCount -->|Yes| CalculateDelay[Calculate Backoff Delay]
    CheckRetryCount -->|No| MaxRetriesReached[Mark as Failed - Max Retries]
    
    CalculateDelay --> ScheduleRetry[Schedule Retry Task]
    ScheduleRetry --> WaitDelay[Wait for Delay Period]
    WaitDelay --> TryExecute
    
    TaskComplete --> End([Task Complete])
    NotRetryable --> End
    MaxRetriesReached --> End
    
    %% Retry delay calculation note
    CalculateDelay -.->|Formula| DelayFormula["delay = min(2^retry_count * 60, 3600) seconds"]
    
    %% Styling
    classDef success fill:#c8e6c9
    classDef error fill:#ffcdd2
    classDef retry fill:#fff3e0
    classDef decision fill:#e1f5fe
    
    class TaskComplete,End success
    class NotRetryable,MaxRetriesReached error
    class CalculateDelay,ScheduleRetry,WaitDelay retry
    class Success,CheckError,IsRetryable,CheckRetryCount decision
```