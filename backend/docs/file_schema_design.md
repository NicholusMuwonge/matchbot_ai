# File Schema Design

## Table Structure

```sql
CREATE TABLE files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  account_id UUID NOT NULL REFERENCES accounts(id),
  filename VARCHAR(255) NOT NULL,
  storage_path TEXT NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  file_size_bytes BIGINT NOT NULL,
  file_hash VARCHAR(64),
  provider VARCHAR(20) NOT NULL DEFAULT 'minio',
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  content JSONB,
  failure_reason TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Field Definitions & Rationale

| Field | Type | Nullable | Reasoning |
|-------|------|----------|-----------|
| **id** | UUID | NOT NULL | Primary key for unique file identification |
| **user_id** | UUID | NOT NULL | Foreign key to users table for ownership |
| **account_id** | UUID | NOT NULL | Multi-tenancy support, account-level isolation |
| **filename** | VARCHAR(255) | NOT NULL | Original user-provided filename for display and search |
| **storage_path** | TEXT | NOT NULL | MinIO/S3 object key for file retrieval |
| **content_type** | VARCHAR(100) | NOT NULL | MIME type (application/pdf, text/csv) for validation and display |
| **file_size_bytes** | BIGINT | NOT NULL | Enforce 20MB limit, billing, storage analytics |
| **file_hash** | VARCHAR(64) | NULLABLE | SHA256 hash for deduplication and integrity verification |
| **provider** | VARCHAR(20) | NOT NULL | Storage backend (minio, s3) for multi-provider support |
| **status** | VARCHAR(50) | NOT NULL | Workflow state: pending, syncing, synced, extracted, failed |
| **content** | JSONB | NULLABLE | Extracted/processed structured data from file |
| **failure_reason** | TEXT | NULLABLE | Error messages for debugging failed uploads/processing |
| **metadata** | JSONB | NULLABLE | Flexible storage for provider-specific and processing metadata |
| **created_at** | TIMESTAMP | NOT NULL | Record creation timestamp |
| **updated_at** | TIMESTAMP | NOT NULL | Last modification timestamp |

## Index Strategy

```sql
-- Primary key (automatic B-tree index)
PRIMARY KEY (id)

-- B-tree indexes for scalar fields
CREATE UNIQUE INDEX idx_files_hash ON files(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX idx_files_filename ON files(filename);
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_account_id ON files(account_id);
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_files_created_at ON files(created_at DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_files_user_created ON files(user_id, created_at DESC);
CREATE INDEX idx_files_account_status ON files(account_id, status);

-- GIN indexes for JSONB containment queries
CREATE INDEX idx_files_content_gin ON files USING GIN(content);
CREATE INDEX idx_files_metadata_gin ON files USING GIN(metadata);
```

## Index Rationale

### B-tree Indexes

| Index | Query Pattern | Performance Benefit |
|-------|--------------|---------------------|
| **idx_files_hash** | `WHERE file_hash = 'sha256...'` | **Deduplication**: Fast exact match for duplicate detection. UNIQUE constraint enforces one file per hash. Partial index (WHERE NOT NULL) saves space. |
| **idx_files_filename** | `WHERE filename = 'report.pdf'`<br>`WHERE filename LIKE 'inv%'` | **Search**: Supports exact match and prefix search. Enables efficient filename filtering in file lists. |
| **idx_files_user_id** | `WHERE user_id = 'uuid'`<br>`JOIN users ON files.user_id = users.id` | **Ownership queries**: Fast retrieval of user's files. Optimizes foreign key joins. |
| **idx_files_account_id** | `WHERE account_id = 'uuid'` | **Multi-tenancy**: Account-level isolation and filtering. Critical for B2B SaaS architecture. |
| **idx_files_status** | `WHERE status = 'pending'`<br>`WHERE status IN ('pending', 'syncing')` | **Workflow filtering**: Find files in specific states. Low cardinality (5-7 values) but frequently queried. |
| **idx_files_created_at** | `ORDER BY created_at DESC`<br>`WHERE created_at > '2025-01-01'` | **Time-range queries**: Pagination, recent files, date filters. DESC index optimizes default sort order. |
| **idx_files_user_created** | `WHERE user_id = 'uuid' ORDER BY created_at DESC LIMIT 20` | **Composite**: User file lists with pagination. Avoids separate index scan + sort. |
| **idx_files_account_status** | `WHERE account_id = 'uuid' AND status = 'failed'` | **Composite**: Account-level status filtering (e.g., "show all failed uploads for account"). |

**Why B-tree?**
- Supports equality (`=`), range (`<`, `>`, `BETWEEN`), sorting (`ORDER BY`)
- Efficient for high-cardinality fields (UUIDs, hashes, timestamps)
- Small memory footprint compared to GIN
- Default index type for most use cases

### GIN Indexes (Generalized Inverted Index)

| Index | Query Pattern | Performance Benefit |
|-------|--------------|---------------------|
| **idx_files_content_gin** | `WHERE content @> '{"status":"matched"}'`<br>`WHERE content ? 'field_name'`<br>`WHERE content->'data'->>'value' = 'X'` | **JSONB queries**: Optimized for containment (`@>`), key existence (`?`), and nested path queries. Enables flexible querying of extracted structured data. |
| **idx_files_metadata_gin** | `WHERE metadata @> '{"storage":{"provider":"minio"}}'`<br>`WHERE metadata->'tags' ? 'urgent'` | **Flexible metadata**: Efficient queries on nested JSON without predefined schema. Supports provider-specific and user-defined fields. |

**Why GIN for JSONB?**
- Optimized for operators: `@>` (contains), `?` (key exists), `?&` (all keys), `?|` (any keys)
- Handles deep nested JSON structures
- Enables schema-less querying on flexible fields
- Essential for JSONB fields that will be queried with containment operators

**Trade-offs:**
- 3x larger than B-tree (stores inverted index of all JSON keys/values)
- Slower writes (index must be updated on every JSON change)
- Worth it for complex JSONB queries, not for simple equality checks

## Field Design Decisions

### Why Native Columns (Not JSONB)?

**filename, content_type, file_size_bytes → Native columns**
- **Frequently queried**: Filter by type, search by name, check size limits
- **B-tree indexable**: Fast equality and range queries
- **Type safety**: Database enforces constraints (VARCHAR length, BIGINT range)
- **Performance**: Direct column access faster than JSONB extraction

### Why VARCHAR for file_hash (Not JSONB)?

**file_hash → VARCHAR(64)**
- **Simple atomic value**: SHA256 is a single string, not nested data
- **Deduplication**: `WHERE file_hash = '...'` needs fast indexed lookup
- **UNIQUE constraint**: Database enforces one file per hash
- **No flexibility needed**: SHA256 is industry standard

### What Goes in content JSONB?

**Extracted/processed structured data:**
```json
{
  "extracted_text": "Invoice #12345...",
  "parsed_data": {
    "invoice_number": "12345",
    "amount": 1500.00,
    "date": "2025-01-15"
  },
  "rows": [...],  // For CSV files
  "matches": [...]  // For processed reconciliation results
}
```

**Purpose**: Store flexible structured output from file processing. Schema varies by file type and extraction method.

### What Goes in metadata JSONB?

**Storage, processing, and contextual metadata:**
```json
{
  "storage": {
    "etag": "d41d8cd98f00b204e9800998ecf8427e",
    "version_id": "3/L4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY",
    "bucket": "user-uploads",
    "region": "us-east-1"
  },
  "upload": {
    "client_ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "upload_method": "web_ui",
    "chunk_size": 5242880
  },
  "processing": {
    "extraction_engine": "tesseract-v5",
    "processing_duration_ms": 3450,
    "confidence_score": 0.95
  },
  "tags": ["invoice", "q1-2025"],
  "custom_fields": {
    "department": "finance",
    "project_code": "PRJ-123"
  }
}
```

**Purpose**:
- Provider-specific details (ETag, version ID)
- Upload context for debugging
- Processing metadata (timings, versions)
- User-defined tags and custom fields
- Non-critical data queried occasionally

**Rule**: If queried in every list/filter, make it a native column. If occasional/flexible, use metadata JSONB.

## Status Enum Values

```python
class FileStatus(str, Enum):
    PENDING = "pending"      # Initial upload state
    SYNCING = "syncing"      # Uploading to MinIO/S3
    SYNCED = "synced"        # Successfully stored
    EXTRACTED = "extracted"  # Text/data extraction complete
    FAILED = "failed"        # Upload or processing error
```

## Common Query Patterns

```sql
-- User's recent files (uses idx_files_user_created)
SELECT * FROM files
WHERE user_id = 'uuid'
ORDER BY created_at DESC
LIMIT 20;

-- Find duplicate file (uses idx_files_hash)
SELECT id FROM files
WHERE file_hash = 'sha256...'
LIMIT 1;

-- Account's failed uploads (uses idx_files_account_status)
SELECT * FROM files
WHERE account_id = 'uuid' AND status = 'failed';

-- Search by filename (uses idx_files_filename)
SELECT * FROM files
WHERE filename ILIKE '%invoice%';

-- Query extracted data (uses idx_files_content_gin)
SELECT * FROM files
WHERE content @> '{"parsed_data": {"amount": 1500}}';

-- Filter by metadata tag (uses idx_files_metadata_gin)
SELECT * FROM files
WHERE metadata->'tags' ? 'urgent';
```

## Performance Considerations

1. **Partial index on file_hash**: `WHERE file_hash IS NOT NULL` saves space since hash may be nullable initially
2. **DESC index on created_at**: Optimizes default "newest first" sort order
3. **Composite indexes**: Avoid multiple index scans for common filter combinations
4. **GIN index size**: Monitor disk usage; GIN indexes are ~3x data size
5. **JSONB compression**: PostgreSQL automatically compresses JSONB, but large content fields may need partitioning

## Migration Notes

- Add indexes CONCURRENTLY in production to avoid table locks
- Monitor query performance and add/remove indexes based on actual usage
- Consider partitioning by created_at if table grows beyond 10M rows
