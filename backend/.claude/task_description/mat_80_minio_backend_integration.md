# MAT-80: Backend MinIO Integration - Detailed Task Description

## Overview
Integrate MinIO object storage with the MatchBot backend API to enable file upload/download capabilities for the reconciliation feature. This integration will provide presigned URLs for secure direct uploads, file metadata tracking, and robust error handling.

## Prerequisites
- MinIO Docker container running and accessible (MAT-63 subtasks completed)
- MinIO buckets initialized (MAT-71 completed)
- Backend API service running in Docker
- PostgreSQL database available for file metadata storage

## Detailed Task Breakdown

### 1. Install MinIO Python SDK
**File**: `backend/requirements.txt`
**Description**: Add the official MinIO Python client library to enable programmatic access to MinIO storage.
```
minio>=7.2.0
python-multipart>=0.0.6  # For file upload handling
```
**Validation**: Run `pip install -r requirements.txt` without errors

---

### 2. Create MinIO Configuration Module
**File**: `backend/app/core/storage_config.py`
**Description**: Centralized configuration for MinIO connection parameters using environment variables.

**Required Environment Variables**:
- `MINIO_ENDPOINT`: MinIO server URL (default: "minio:9000" for Docker network)
- `MINIO_ACCESS_KEY`: Access key for authentication
- `MINIO_SECRET_KEY`: Secret key for authentication
- `MINIO_SECURE`: Use HTTPS (default: False for development)
- `MINIO_REGION`: Region configuration (default: "us-east-1")
- `MINIO_BUCKET_RECONCILIATION`: Bucket name for reconciliation files (default: "reconciliation-files")

**Implementation Requirements**:
- Use Pydantic Settings for type validation
- Support both Docker network names and localhost access
- Provide sensible defaults for development
- Validate configuration on startup

---

### 3. Implement MinIO Client Service
**File**: `backend/app/services/storage/minio_client.py`
**Description**: Core service class managing MinIO client lifecycle and connections.

**Key Features**:
- Singleton pattern to reuse connections
- Connection pooling for concurrent operations
- Automatic reconnection on failure
- Thread-safe operations
- Graceful shutdown handling

**Methods to Implement**:
```python
class MinIOClientService:
    def __init__(self, config: StorageConfig)
    def get_client(self) -> Minio
    def verify_connection(self) -> bool
    def ensure_bucket_exists(self, bucket_name: str) -> bool
    def close(self) -> None
```

---

### 4. Create Presigned URL Service for Uploads
**File**: `backend/app/services/storage/presigned_url_service.py`
**Description**: Generate secure, time-limited URLs for direct file uploads to MinIO.

**Method Signature**:
```python
def generate_upload_url(
    bucket_name: str,
    object_name: str,
    expires_in: int = 3600,  # 1 hour default
    content_type: str = None,
    max_file_size: int = None
) -> Dict[str, Any]
```

**Returns**:
```json
{
    "upload_url": "https://...",
    "file_id": "uuid",
    "expires_at": "2024-01-01T12:00:00Z",
    "method": "PUT",
    "headers": {
        "Content-Type": "text/csv"
    }
}
```

**Security Considerations**:
- Validate file extensions (.csv, .xlsx only for MVP)
- Set maximum file size (100MB default)
- Include content-type restrictions
- Generate unique object names to prevent overwrites

---

### 5. Create Presigned URL Service for Downloads
**File**: `backend/app/services/storage/presigned_url_service.py` (same file as uploads)
**Description**: Generate secure URLs for downloading files from MinIO.

**Method Signature**:
```python
def generate_download_url(
    bucket_name: str,
    object_name: str,
    expires_in: int = 7200,  # 2 hours default
    filename: str = None  # Original filename for Content-Disposition
) -> Dict[str, Any]
```

**Features**:
- Set Content-Disposition header for proper filename
- Longer expiry for downloads vs uploads
- Track download attempts (optional)

---

### 6. Implement File Metadata Tracking Service
**File**: `backend/app/services/storage/file_metadata_service.py`
**Description**: Manage file metadata in PostgreSQL, tracking upload states and file information.

**Database Schema** (`file_uploads` table):
```sql
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    reconciliation_id UUID REFERENCES reconciliations(id),
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    content_type VARCHAR(100),
    file_size_bytes BIGINT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Status values: pending, uploading, uploaded, confirmed, processing, ready, failed
    upload_started_at TIMESTAMP,
    upload_completed_at TIMESTAMP,
    file_hash VARCHAR(64),  -- SHA256 hash
    row_count INTEGER,
    error_message TEXT,
    metadata JSONB,  -- Additional flexible metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_file_uploads_user_id ON file_uploads(user_id);
CREATE INDEX idx_file_uploads_reconciliation_id ON file_uploads(reconciliation_id);
CREATE INDEX idx_file_uploads_status ON file_uploads(status);
```

**Service Methods**:
- `create_file_record()` - Initialize file upload tracking
- `update_file_status()` - Track upload progress
- `confirm_upload()` - Mark file as successfully uploaded
- `get_file_status()` - Retrieve current file state
- `link_to_reconciliation()` - Associate file with reconciliation

---

### 7. POST /files/sign_upload Endpoint
**File**: `backend/app/api/v1/endpoints/files.py`
**Description**: API endpoint to request presigned URL for file upload.

**Request Body**:
```json
{
    "reconciliation_id": "uuid",  // Optional for initial upload
    "file_type": "source|comparison",
    "filename": "transactions.csv",
    "content_type": "text/csv",
    "file_size_bytes": 1048576
}
```

**Response**:
```json
{
    "file_id": "uuid",
    "upload_url": "https://...",
    "expires_at": "2024-01-01T12:00:00Z",
    "method": "PUT",
    "headers": {
        "Content-Type": "text/csv",
        "Content-Length": "1048576"
    }
}
```

**Validation**:
- Authenticate user
- Validate file type and size
- Check reconciliation ownership
- Rate limiting (10 requests per minute)

---

### 8. POST /files/confirm Endpoint
**File**: `backend/app/api/v1/endpoints/files.py`
**Description**: Confirm successful file upload and trigger processing.

**Request Body**:
```json
{
    "file_id": "uuid",
    "reconciliation_id": "uuid",  // Link file to reconciliation
    "metadata": {
        "columns": ["date", "amount", "description"],
        "row_count": 1000,
        "file_hash": "sha256..."
    }
}
```

**Processing Steps**:
1. Verify file exists in MinIO
2. Validate file size matches expected
3. Update file status to 'confirmed'
4. Link to reconciliation if provided
5. Trigger async extraction job (future task)

---

### 9. GET /files/:id/status Endpoint
**File**: `backend/app/api/v1/endpoints/files.py`
**Description**: Check current status of file upload/processing.

**Response**:
```json
{
    "file_id": "uuid",
    "status": "ready",
    "filename": "transactions.csv",
    "file_size_bytes": 1048576,
    "row_count": 1000,
    "uploaded_at": "2024-01-01T11:00:00Z",
    "processed_at": "2024-01-01T11:05:00Z",
    "error_message": null
}
```

---

### 10. Bucket Verification and Creation Logic
**File**: `backend/app/services/storage/bucket_manager.py`
**Description**: Ensure required buckets exist on application startup.

**Implementation**:
```python
class BucketManager:
    def initialize_buckets(self):
        """Create buckets if they don't exist"""
        required_buckets = [
            "reconciliation-files",
            "reconciliation-reports",
            "temp-uploads"
        ]
        for bucket in required_buckets:
            self.ensure_bucket_exists(bucket)
            self.set_bucket_policy(bucket)
            self.configure_lifecycle_rules(bucket)
```

**Lifecycle Rules**:
- Delete unconfirmed files after 24 hours
- Archive completed reconciliation files after 30 days
- Purge temp files after 1 hour

---

### 11. Error Handling and Retry Mechanisms
**File**: `backend/app/services/storage/resilience.py`
**Description**: Implement robust error handling for storage operations.

**Key Components**:
- Exponential backoff for retries
- Circuit breaker pattern for repeated failures
- Specific exception handling for MinIO errors
- Fallback strategies (e.g., queue for later)

**Error Types to Handle**:
- Network timeouts
- Connection refused
- Invalid credentials
- Bucket not found
- Access denied
- Storage quota exceeded

**Retry Configuration**:
```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_delay": 1,  # seconds
    "max_delay": 30,
    "exponential_base": 2,
    "jitter": True
}
```

---

### 12. Health Check Endpoint for MinIO
**File**: `backend/app/api/v1/endpoints/health.py`
**Description**: Endpoint to verify MinIO connectivity and configuration.

**Endpoint**: `GET /health/storage`

**Response**:
```json
{
    "status": "healthy",
    "storage_backend": "minio",
    "endpoint": "minio:9000",
    "buckets_accessible": [
        "reconciliation-files",
        "reconciliation-reports"
    ],
    "response_time_ms": 45,
    "errors": []
}
```

**Health Checks**:
- Can connect to MinIO
- Can list buckets
- Can perform test upload/download
- Response time within threshold

---

### 13. Unit Tests for MinIO Service
**File**: `backend/tests/services/storage/test_minio_client.py`
**Description**: Comprehensive unit tests with mocked MinIO client.

**Test Coverage**:
- Connection establishment
- Presigned URL generation
- Error handling scenarios
- Retry logic
- File metadata operations
- Bucket operations

**Testing Strategy**:
- Use `unittest.mock` to mock MinIO client
- Test both success and failure paths
- Validate URL format and expiration
- Test concurrent operations

---

### 14. Integration Test Script
**File**: `backend/tests/integration/test_storage_integration.py`
**Description**: End-to-end test of file upload/download flow with real MinIO.

**Test Scenario**:
1. Request presigned upload URL
2. Upload file using presigned URL
3. Confirm upload
4. Verify file exists in MinIO
5. Request download URL
6. Download and verify file content
7. Clean up test files

**Requirements**:
- Requires MinIO running (Docker)
- Uses test bucket
- Includes performance benchmarks
- Tests error scenarios

---

### 15. Logging and Monitoring
**File**: `backend/app/services/storage/monitoring.py`
**Description**: Implement comprehensive logging and metrics for storage operations.

**Metrics to Track**:
- Upload/download success rate
- Average file size
- Operation latency
- Error rates by type
- Storage usage per user
- Concurrent operations

**Log Format**:
```python
logger.info(
    "Storage operation completed",
    extra={
        "operation": "upload",
        "file_id": "uuid",
        "user_id": "uuid",
        "file_size": 1048576,
        "duration_ms": 234,
        "bucket": "reconciliation-files",
        "status": "success"
    }
)
```

**Monitoring Integration**:
- Structured logging (JSON format)
- Prometheus metrics endpoint
- Alert on high error rates
- Dashboard for storage metrics

---

## Implementation Order

1. **Phase 1 - Core Infrastructure** (Tasks 1-3)
   - Install SDK
   - Create configuration
   - Implement client service

2. **Phase 2 - Basic Operations** (Tasks 4-6, 10)
   - Presigned URLs
   - File metadata
   - Bucket management

3. **Phase 3 - API Endpoints** (Tasks 7-9)
   - Sign upload endpoint
   - Confirm endpoint
   - Status endpoint

4. **Phase 4 - Robustness** (Tasks 11-12, 15)
   - Error handling
   - Health checks
   - Monitoring

5. **Phase 5 - Testing** (Tasks 13-14)
   - Unit tests
   - Integration tests

---

## Success Criteria

- [ ] MinIO client successfully connects from backend container
- [ ] Presigned URLs work for both upload and download
- [ ] File metadata is tracked in PostgreSQL
- [ ] API endpoints return appropriate responses
- [ ] Error handling prevents application crashes
- [ ] Health check accurately reports storage status
- [ ] Unit tests achieve >80% coverage
- [ ] Integration test passes end-to-end
- [ ] Monitoring provides visibility into operations

---

## Notes and Considerations

1. **Security**: Never expose MinIO credentials in logs or responses
2. **Performance**: Use connection pooling for high throughput
3. **Compatibility**: Ensure S3-compatible API for future AWS migration
4. **Documentation**: Update API documentation with new endpoints
5. **Migration Path**: Design with future S3 migration in mind

---

## Frontend Client Flow

### How the Frontend Uses the Presigned URL API

```typescript
// 1. USER SELECTS FILE IN UI
const handleFileSelect = async (file: File) => {
  try {
    // 2. REQUEST PRESIGNED URL FROM BACKEND
    const presignResponse = await fetch('/api/files/sign_upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        filename: file.name,
        file_type: 'source',  // or 'comparison'
        reconciliation_id: currentReconciliationId  // optional
      })
    });

    const presignData = await presignResponse.json();
    /*
    presignData = {
      upload_url: "http://minio:9000/temp-bucket",
      form_fields: {
        key: "temp/user123/source/20240124_142530_uuid.csv",
        policy: "...",
        "x-amz-algorithm": "...",
        "x-amz-credential": "...",
        "x-amz-date": "...",
        "x-amz-signature": "..."
      },
      file_id: "uuid-1234",
      object_name: "temp/user123/source/20240124_142530_uuid.csv",
      bucket_name: "temp-bucket"
    }
    */

    // 3. UPLOAD DIRECTLY TO MINIO/S3 USING PRESIGNED URL
    const formData = new FormData();

    // Add all form fields from presigned response (ORDER MATTERS!)
    Object.entries(presignData.form_fields).forEach(([key, value]) => {
      formData.append(key, value as string);
    });

    // File must be last!
    formData.append('file', file);

    const uploadResponse = await fetch(presignData.upload_url, {
      method: 'POST',
      body: formData
      // No auth header needed - signature is in form fields
    });

    if (!uploadResponse.ok) {
      throw new Error('Upload failed');
    }

    // 4. CONFIRM UPLOAD WITH BACKEND (triggers processing)
    const confirmResponse = await fetch('/api/files/confirm', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file_id: presignData.file_id,
        object_name: presignData.object_name,
        bucket_name: presignData.bucket_name,
        reconciliation_id: currentReconciliationId,  // optional, can link later
        metadata: {
          original_filename: file.name,
          size: file.size,
          type: file.type
        }
      })
    });

    const confirmData = await confirmResponse.json();
    /*
    confirmData = {
      status: "confirmed",
      file_ingestion_id: "db-uuid",
      processing_status: "queued"  // Backend starts streaming/processing
    }
    */

    // 5. POLL FOR PROCESSING STATUS (optional)
    pollFileStatus(confirmData.file_ingestion_id);

  } catch (error) {
    console.error('Upload error:', error);
  }
};

// Optional: Poll for file processing status
const pollFileStatus = async (fileIngestionId: string) => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/files/${fileIngestionId}/status`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    const data = await response.json();
    /*
    data = {
      status: "processing" | "ready" | "failed",
      row_count: 1234,
      error: null
    }
    */

    if (data.status === 'ready' || data.status === 'failed') {
      clearInterval(interval);
      // Update UI accordingly
    }
  }, 2000);
};
```

### Visual Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────┐
│   Frontend  │     │  Backend API │     │ MinIO/S3    │     │  Database  │
└──────┬──────┘     └──────┬───────┘     └──────┬──────┘     └─────┬──────┘
       │                    │                     │                  │
   [1] │ Select File        │                     │                  │
       │                    │                     │                  │
   [2] │──POST /sign_upload─>                     │                  │
       │    (filename)      │                     │                  │
       │                    │                     │                  │
       │<──Presigned URL────│                     │                  │
       │   + form fields    │                     │                  │
       │                    │                     │                  │
   [3] │────────POST file───────────────────────>│                  │
       │   (direct upload)  │                     │                  │
       │                    │                     │                  │
       │<───────204 OK──────────────────────────│                  │
       │                    │                     │                  │
   [4] │──POST /confirm────>│                     │                  │
       │   (file_id)        │                     │                  │
       │                    │──────────────────────────────────────>│
       │                    │  Create file_ingestion record         │
       │                    │                     │                  │
       │                    │──GET file stream──>│                  │
       │                    │   (background)      │                  │
       │                    │<────File data──────│                  │
       │                    │                     │                  │
       │                    │──────────────────────────────────────>│
       │                    │  Process & store transactions         │
       │                    │                     │                  │
       │<──Confirmed────────│                     │                  │
       │                    │                     │                  │
   [5] │──GET /status──────>│                     │                  │
       │   (polling)        │──────────────────────────────────────>│
       │                    │<───────────────────────────────────────│
       │<──Processing───────│                     │                  │
       │                    │                     │                  │
```

### Key Points
1. Frontend never needs MinIO/S3 credentials
2. File goes directly to storage (no backend proxy)
3. Confirm endpoint triggers backend processing
4. File can be linked to reconciliation during confirm or later