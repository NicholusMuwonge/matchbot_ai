#!/usr/bin/env python
"""
Test script for MinIO integration.
Run this to verify MinIO connection and basic operations work.
"""

import os
import sys
from io import BytesIO

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.services.minio_service import MinIOService


def test_minio_connection():
    """Test MinIO connection and basic operations."""
    print("Testing MinIO Integration")
    print("=" * 50)
    print(f"Endpoint: {settings.MINIO_ENDPOINT}")
    print(f"Bucket: {settings.MINIO_BUCKET_NAME}")
    print(f"SSL: {settings.MINIO_USE_SSL}")
    print("=" * 50)

    try:
        # Initialize service
        print("\n1. Initializing MinIO service...")
        service = MinIOService()
        print("✅ Service initialized successfully")

        # Test upload
        print("\n2. Testing file upload...")
        test_data = b"Hello MinIO from Backend!"
        test_file = BytesIO(test_data)
        object_name = "test/backend-test.txt"

        service.upload_file(
            test_file,
            object_name,
            content_type="text/plain",
            metadata={"source": "backend-test"},
        )
        print(f"✅ Uploaded test file: {object_name}")

        # Test file existence
        print("\n3. Testing file existence check...")
        exists = service.object_exists(object_name)
        print(f"✅ File exists: {exists}")

        # Test metadata retrieval
        print("\n4. Testing metadata retrieval...")
        metadata = service.get_object_metadata(object_name)
        print(
            f"✅ File metadata: size={metadata['size']} bytes, type={metadata['content_type']}"
        )

        # Test presigned URLs
        print("\n5. Testing presigned URL generation...")
        upload_url = service.generate_presigned_upload_url("test/upload-test.txt")
        print(f"✅ Upload URL generated: {upload_url[:50]}...")

        download_url = service.generate_presigned_download_url(object_name)
        print(f"✅ Download URL generated: {download_url[:50]}...")

        # Test download
        print("\n6. Testing file download...")
        downloaded_data = service.download_file(object_name)
        content = downloaded_data.read()
        print(f"✅ Downloaded file content: {content.decode()}")

        # Test listing
        print("\n7. Testing file listing...")
        files = service.list_objects(prefix="test/")
        print(f"✅ Found {len(files)} files with prefix 'test/'")
        for f in files:
            print(f"   - {f['name']} ({f['size']} bytes)")

        # Test deletion
        print("\n8. Testing file deletion...")
        service.delete_file(object_name)
        print(f"✅ Deleted test file: {object_name}")

        # Verify deletion
        exists_after = service.object_exists(object_name)
        print(f"✅ File exists after deletion: {exists_after}")

        print("\n" + "=" * 50)
        print("✅ All MinIO tests passed successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    # Set MinIO endpoint for local testing if needed
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        os.environ["MINIO_ENDPOINT"] = "localhost:9000"
        print("Using local MinIO endpoint: localhost:9000\n")

    success = test_minio_connection()
    sys.exit(0 if success else 1)
