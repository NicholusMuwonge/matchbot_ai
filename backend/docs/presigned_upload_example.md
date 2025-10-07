# Presigned Upload Flow - Frontend Example

## API Endpoints

### Single File Upload
- **Endpoint:** `POST /api/v1/files/presigned-upload`
- **Auth:** Bearer token required

### Bulk File Upload
- **Endpoint:** `POST /api/v1/files/presigned-uploads`
- **Auth:** Bearer token required

---

## Flow Example

### Step 1: Frontend Sends Request

**Request to Backend:**
```javascript
// Single file
POST /api/v1/files/presigned-upload
Headers: {
  "Authorization": "Bearer <clerk-token>",
  "Content-Type": "application/json"
}
Body: {
  "filename": "resume.pdf"
}

// Multiple files
POST /api/v1/files/presigned-uploads
Headers: {
  "Authorization": "Bearer <clerk-token>",
  "Content-Type": "application/json"
}
Body: {
  "files": [
    {"filename": "resume.pdf"},
    {"filename": "photo.jpg"},
    {"filename": "transcript.pdf"}
  ]
}
```

### Step 2: Backend Returns Presigned URL(s)

**Response from Backend (Single):**
```json
{
  "upload_url": "https://minio.example.com:9000/reconciliation-files",
  "form_fields": {
    "key": "files/user-abc123/shared_files/source/20250103_142530_xyz789.pdf",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-credential": "minioadmin/20250103/us-east-1/s3/aws4_request",
    "x-amz-date": "20250103T142530Z",
    "policy": "eyJleHBpcmF0aW9uIjoiMjAyNS0wMS0wM1QxNToyNTozMFoiLCJjb25kaXRpb25zIjpbWyJlcSIsIiRrZXkiLCJmaWxlcy91c2VyLWFiYzEyMy9zaGFyZWRfZmlsZXMvc291cmNlLzIwMjUwMTAzXzE0MjUzMF94eXo3ODkucGRmIl0sWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsMSwxMDQ4NTc2MDBdXX0=",
    "x-amz-signature": "abcd1234567890efgh",
    "Content-Type": "application/pdf"
  },
  "file_id": "xyz789",
  "object_name": "files/user-abc123/shared_files/source/20250103_142530_xyz789.pdf",
  "bucket_name": "reconciliation-files",
  "original_filename": "resume.pdf",
  "content_type": "application/pdf",
  "expires_at": "2025-01-03T15:25:30Z",
  "max_file_size": 104857600,
  "allowed_extensions": [".csv", ".xlsx", ".pdf", ".jpg", ".png", ".doc", ".docx"],
  "instructions": {
    "method": "POST",
    "enctype": "multipart/form-data",
    "field_order": ["key", "x-amz-algorithm", "x-amz-credential", "x-amz-date", "policy", "x-amz-signature", "Content-Type", "file"],
    "note": "File field must be last in form submission"
  }
}
```

**Response from Backend (Bulk):**
```json
[
  {
    "upload_url": "https://minio.example.com:9000/reconciliation-files",
    "form_fields": { /* same as above */ },
    "file_id": "xyz789",
    "original_filename": "resume.pdf",
    // ... rest of fields
  },
  {
    "upload_url": "https://minio.example.com:9000/reconciliation-files",
    "form_fields": { /* different signature */ },
    "file_id": "abc456",
    "original_filename": "photo.jpg",
    // ... rest of fields
  }
  // ... more files
]
```

### Step 3: Frontend Uploads to MinIO

**Upload to MinIO (multipart/form-data POST):**

The frontend must:
1. Create a FormData object
2. Add all `form_fields` in the correct order
3. Add the file **last**
4. POST to `upload_url`

---

## Frontend Implementation

### React/TypeScript Example

```typescript
import axios from 'axios';

interface PresignedUploadResponse {
  upload_url: string;
  form_fields: Record<string, string>;
  file_id: string;
  object_name: string;
  original_filename: string;
  expires_at: string;
  instructions: {
    field_order: string[];
    method: string;
    enctype: string;
    note: string;
  };
}

// Step 1: Get presigned URL from backend
async function getPresignedUploadUrl(
  filename: string,
  authToken: string
): Promise<PresignedUploadResponse> {
  const response = await axios.post(
    '/api/v1/files/presigned-upload',
    { filename },
    {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return response.data;
}

// Step 2: Upload file to MinIO using presigned URL
async function uploadToMinIO(
  file: File,
  presignedData: PresignedUploadResponse
): Promise<void> {
  const formData = new FormData();

  // Add all form fields in the specified order (IMPORTANT!)
  presignedData.instructions.field_order.forEach((fieldName) => {
    if (fieldName !== 'file' && presignedData.form_fields[fieldName]) {
      formData.append(fieldName, presignedData.form_fields[fieldName]);
    }
  });

  // Add file LAST (critical requirement)
  formData.append('file', file);

  // POST to MinIO
  await axios.post(presignedData.upload_url, formData, {
    headers: {
      // Don't set Content-Type - browser will set it with boundary
    },
  });
}

// Complete upload flow
async function uploadFile(file: File, authToken: string): Promise<string> {
  try {
    // Step 1: Get presigned URL
    const presignedData = await getPresignedUploadUrl(file.name, authToken);

    console.log('Presigned URL obtained:', presignedData.file_id);
    console.log('Expires at:', presignedData.expires_at);

    // Step 2: Upload to MinIO
    await uploadToMinIO(file, presignedData);

    console.log('Upload successful!');

    // Step 3: Return file_id for backend notification (future endpoint)
    return presignedData.file_id;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
}

// Bulk upload example
async function uploadMultipleFiles(
  files: File[],
  authToken: string
): Promise<string[]> {
  try {
    // Step 1: Get presigned URLs for all files
    const response = await axios.post(
      '/api/v1/files/presigned-uploads',
      {
        files: files.map(f => ({ filename: f.name }))
      },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    const presignedDataList: PresignedUploadResponse[] = response.data;

    // Step 2: Upload all files in parallel
    const uploadPromises = presignedDataList.map((presignedData, index) =>
      uploadToMinIO(files[index], presignedData)
    );

    await Promise.all(uploadPromises);

    console.log('All uploads successful!');

    // Step 3: Return file_ids
    return presignedDataList.map(d => d.file_id);
  } catch (error) {
    console.error('Bulk upload failed:', error);
    throw error;
  }
}

// Usage in a component
function FileUploader() {
  const { getToken } = useAuth(); // Clerk hook

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    const authToken = await getToken();

    try {
      if (files.length === 1) {
        const fileId = await uploadFile(files[0], authToken);
        console.log('Uploaded file ID:', fileId);
      } else {
        const fileIds = await uploadMultipleFiles(files, authToken);
        console.log('Uploaded file IDs:', fileIds);
      }

      // TODO: Notify backend that upload is complete
      // POST /api/v1/files/{file_id}/complete
    } catch (error) {
      alert('Upload failed. Please try again.');
    }
  };

  return (
    <input
      type="file"
      multiple
      onChange={handleFileUpload}
      accept=".csv,.xlsx,.pdf,.jpg,.png,.doc,.docx"
    />
  );
}
```

---

## Key Points

1. **Order matters:** Form fields must be added in the order specified by `instructions.field_order`
2. **File goes last:** The file input must be the last field in the FormData
3. **Direct upload:** Files go directly to MinIO, not through your backend
4. **No Content-Type header:** Let the browser set it automatically with multipart boundary
5. **Parallel uploads:** Multiple files can upload simultaneously
6. **Atomic operation:** If any presigned URL generation fails, entire bulk request fails
7. **Expiration:** URLs expire after 1 hour (configurable)
8. **Size limit:** Default max file size is 100MB

---

## Error Handling

### Backend Errors (Step 1)
```json
{
  "detail": "File type not allowed. Allowed extensions: .csv, .xlsx, .pdf, .jpg, .png"
}
```

### MinIO Upload Errors (Step 2)
- 403 Forbidden: Signature expired or invalid
- 400 Bad Request: File size exceeds limit or policy violation
- 500 Server Error: MinIO service issue
