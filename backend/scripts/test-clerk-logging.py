#!/usr/bin/env python3
"""
Test script for Clerk SDK logging integration

This script demonstrates the logging capabilities added to the ClerkService.
It shows different log levels and how to enable debug logging.

Usage:
    # Basic logging (warnings and errors only)
    python scripts/test-clerk-logging.py

    # Enable debug logging via environment variable
    CLERK_DEBUG=true python scripts/test-clerk-logging.py

    # Enable debug logging with actual API key
    CLERK_SECRET_KEY=sk_test_your_key CLERK_DEBUG=true python scripts/test-clerk-logging.py
"""

import logging
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def setup_logging():
    """Set up comprehensive logging configuration"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def test_clerk_service_logging():
    """Test ClerkService logging functionality"""
    print("🧪 Testing Clerk Service Logging Integration\n")

    try:
        from app.services.clerk_auth import ClerkAuthenticationError, ClerkService

        print("✅ Successfully imported ClerkService")

        # Test 1: Create service without API key (should fail gracefully)
        print("\n📋 Test 1: Attempting to create service without API key")
        try:
            service = ClerkService()
            print("❌ Unexpected: Service created without API key")
        except ClerkAuthenticationError as e:
            print(f"✅ Expected error: {e}")

        # Test 2: Create service with fake API key (should show logging setup)
        print("\n📋 Test 2: Creating service with fake API key")
        os.environ["CLERK_SECRET_KEY"] = "sk_test_fake_key_for_testing_logging"

        try:
            service = ClerkService()
            print("✅ Service created successfully with debug logging")

            # Test 3: Test session validation (will fail but show logging)
            print("\n📋 Test 3: Testing session validation with fake token")
            try:
                result = service.validate_session_token(
                    "fake_session_token_for_testing"
                )
                print("❌ Unexpected success with fake token")
            except ClerkAuthenticationError as e:
                print(f"✅ Expected validation error: {e}")

            # Test 4: Test user fetch (will fail but show logging)
            print("\n📋 Test 4: Testing user fetch with fake user ID")
            try:
                result = service.get_user("fake_user_id_for_testing")
                print(f"📊 Result: {result}")
            except ClerkAuthenticationError as e:
                print(f"✅ Expected fetch error: {e}")

        except Exception as e:
            print(f"❌ Unexpected error creating service: {e}")

    except ImportError as e:
        print(f"❌ Failed to import ClerkService: {e}")
        return False

    return True


def show_logging_configuration():
    """Show current logging configuration"""
    print("\n📊 Current Logging Configuration:")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'local')}")
    print(f"   CLERK_DEBUG: {os.getenv('CLERK_DEBUG', 'false')}")
    print(
        f"   CLERK_SECRET_KEY: {'✅ Set' if os.getenv('CLERK_SECRET_KEY') else '❌ Not set'}"
    )

    # Show active loggers
    clerk_service_logger = logging.getLogger("clerk_service")
    clerk_api_logger = logging.getLogger("clerk_backend_api")

    print(
        f"   clerk_service logger level: {logging.getLevelName(clerk_service_logger.level)}"
    )
    print(
        f"   clerk_backend_api logger level: {logging.getLevelName(clerk_api_logger.level)}"
    )


def main():
    """Main test function"""
    print("🔧 Clerk SDK Logging Integration Test")
    print("=" * 50)

    setup_logging()
    show_logging_configuration()

    success = test_clerk_service_logging()

    print("\n" + "=" * 50)
    if success:
        print("✅ All logging tests completed successfully!")
        print("\n💡 Tips:")
        print("   • Set CLERK_DEBUG=true for detailed SDK logging")
        print("   • Logs will show API calls, responses, and errors")
        print("   • Use with real API keys for actual Clerk integration testing")
    else:
        print("❌ Some tests failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
