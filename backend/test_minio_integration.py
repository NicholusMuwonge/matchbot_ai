#!/usr/bin/env python3
"""
Test script for MinIO storage integration.
Run this to verify MinIO services are working correctly.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.storage import (
    MinIOStorageException,
    bucket_manager,
    minio_client_service,
    presigned_url_service,
)


def test_connection():
    """Test MinIO connection"""
    print("\n1. Testing MinIO Connection...")
    try:
        connected = minio_client_service.verify_connection()
        if connected:
            print("   ✓ Successfully connected to MinIO")
            return True
        else:
            print("   ✗ Failed to connect to MinIO")
            return False
    except Exception as e:
        print(f"   ✗ Connection error: {e}")
        return False


def test_bucket_initialization():
    """Test bucket initialization"""
    print("\n2. Testing Bucket Initialization...")
    try:
        success = bucket_manager.initialize_buckets()
        if success:
            print("   ✓ All buckets initialized successfully")
            return True
        else:
            print("   ✗ Some buckets failed to initialize")
            return False
    except Exception as e:
        print(f"   ✗ Bucket initialization error: {e}")
        return False


def test_presigned_upload():
    """Test presigned URL generation for uploads"""
    print("\n3. Testing Presigned Upload URL Generation...")
    try:
        # Test CSV upload with reconciliation_id (tied to specific reconciliation)
        upload_info = presigned_url_service.generate_upload_url(
            filename="test_data.csv",
            file_type="source",
            reconciliation_id="test-recon-123",
            user_id="test-user-456",
        )

        print("   ✓ Generated upload URL for CSV file (with reconciliation_id)")
        print(f"   - File ID: {upload_info['file_id']}")
        print(f"   - Object path: {upload_info['object_name']}")
        print(f"   - Upload URL: {upload_info['upload_url']}")
        print(f"   - Expires at: {upload_info['expires_at']}")
        print(f"   - Max size: {upload_info['max_file_size']} bytes")

        # Test XLSX upload without reconciliation_id (reusable file)
        xlsx_info = presigned_url_service.generate_upload_url(
            filename="reusable_data.xlsx",
            file_type="comparison",
            user_id="test-user-456",  # No reconciliation_id - file can be reused
        )
        print("   ✓ Generated upload URL for reusable XLSX file (no reconciliation_id)")
        print(f"   - Object path: {xlsx_info['object_name']}")
        print("   - Can be linked to multiple reconciliations later")

        # Test upload without user_id and reconciliation_id (should fail)
        try:
            invalid_info = presigned_url_service.generate_upload_url(
                filename="test.csv", file_type="source"
            )
            print(
                "   ✗ Should have required user_id when reconciliation_id not provided"
            )
            return False
        except MinIOStorageException as e:
            if "user_id is required" in str(e):
                print("   ✓ Correctly enforced user_id requirement for reusable files")
            else:
                print(f"   ✗ Wrong error: {e}")
                return False

        return True

    except MinIOStorageException as e:
        print(f"   ✗ Upload URL generation error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False


def test_invalid_file_type():
    """Test rejection of invalid file types"""
    print("\n4. Testing Invalid File Type Rejection...")
    try:
        upload_info = presigned_url_service.generate_upload_url(
            filename="test.pdf", file_type="source"
        )
        print("   ✗ Should have rejected PDF file")
        return False

    except MinIOStorageException as e:
        if "not allowed" in str(e):
            print("   ✓ Correctly rejected invalid file type (PDF)")
            return True
        else:
            print(f"   ✗ Wrong error: {e}")
            return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False


def test_bucket_health():
    """Test bucket health check"""
    print("\n5. Testing Bucket Health Check...")
    try:
        health = bucket_manager.verify_buckets_health()

        print(
            f"   Health Status: {'✓ Healthy' if health['healthy'] else '✗ Unhealthy'}"
        )

        for bucket_name, status in health.get("buckets", {}).items():
            if status.get("exists"):
                print(f"   ✓ {bucket_name}: exists and accessible")
            else:
                print(f"   ✗ {bucket_name}: {status.get('error', 'not found')}")

        if health.get("errors"):
            print(f"   Errors: {health['errors']}")

        return health["healthy"]

    except Exception as e:
        print(f"   ✗ Health check error: {e}")
        return False


def test_file_operations():
    """Test file listing"""
    print("\n6. Testing File Operations...")
    try:
        from app.core.storage_config import storage_config

        # List files in temp bucket
        temp_files = minio_client_service.list_files(
            storage_config.MINIO_BUCKET_TEMP, prefix="temp/"
        )

        print(f"   Found {len(temp_files)} files in temp bucket")

        if temp_files:
            print("   Sample files:")
            for f in temp_files[:3]:
                print(f"   - {f['key']} ({f['size']} bytes)")

        return True

    except Exception as e:
        print(f"   ✗ File listing error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("MinIO Storage Integration Test")
    print("=" * 60)

    tests = [
        test_connection,
        test_bucket_initialization,
        test_presigned_upload,
        test_invalid_file_type,
        test_bucket_health,
        test_file_operations,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test_func.__name__} failed with: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
