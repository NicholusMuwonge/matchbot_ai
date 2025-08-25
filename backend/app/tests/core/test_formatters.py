"""
Tests for formatters module
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.formatters import ClerkDataFormatter


class TestClerkDataFormatter:
    """Test ClerkDataFormatter functionality"""

    @pytest.fixture
    def sample_clerk_user(self):
        """Create a sample Clerk SDK User object for testing"""
        # Mock a Clerk SDK User object with the expected attributes
        user = MagicMock()
        user.id = "user_2abc123def456"
        user.first_name = "John"
        user.last_name = "Doe"
        user.has_image = False
        user.image_url = None
        user.created_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        user.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        # Mock email addresses structure as it exists in Clerk SDK
        email_obj = MagicMock()
        email_obj.id = "idn_test_email"
        email_obj.email_address = "test@example.com"

        user.email_addresses = [email_obj]
        user.primary_email_address_id = "idn_test_email"

        return user

    def test_format_user_data(self, sample_clerk_user):
        """Test format_user_data returns correctly formatted user data"""
        result = ClerkDataFormatter.format_user_data(sample_clerk_user)

        # Check that all expected fields are present
        expected_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "image_url",
            "has_image",
            "created_at",
            "updated_at",
        ]

        for field in expected_fields:
            assert field in result, f"Field {field} missing from formatted data"

        # Check that values are correctly mapped
        assert result["id"] == sample_clerk_user.id
        assert (
            result["email"] == "test@example.com"
        )  # Should extract from email_addresses
        assert result["first_name"] == sample_clerk_user.first_name
        assert result["last_name"] == sample_clerk_user.last_name
        assert result["created_at"] == sample_clerk_user.created_at
        assert result["updated_at"] == sample_clerk_user.updated_at

    def test_format_user_data_with_no_image(self, sample_clerk_user):
        """Test format_user_data handles users without images"""
        sample_clerk_user.has_image = False
        sample_clerk_user.image_url = None

        result = ClerkDataFormatter.format_user_data(sample_clerk_user)

        assert result["has_image"] is False
        assert result["image_url"] is None

    def test_format_user_data_with_image(self, sample_clerk_user):
        """Test format_user_data handles users with images"""
        sample_clerk_user.has_image = True
        sample_clerk_user.image_url = "https://example.com/image.jpg"

        result = ClerkDataFormatter.format_user_data(sample_clerk_user)

        assert result["has_image"] is True
        assert result["image_url"] == "https://example.com/image.jpg"

    def test_format_user_data_handles_missing_primary_email(self):
        """Test format_user_data gracefully handles missing primary email"""
        user = MagicMock()
        user.id = "user_minimal123"
        user.first_name = "Jane"
        user.last_name = "Smith"
        user.has_image = False
        user.image_url = None
        user.created_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        user.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        # Mock email addresses but no primary match
        email_obj = MagicMock()
        email_obj.id = "idn_different_email"
        email_obj.email_address = "fallback@example.com"

        user.email_addresses = [email_obj]
        user.primary_email_address_id = "idn_nonexistent"  # Doesn't match any email

        result = ClerkDataFormatter.format_user_data(user)

        # Should fallback to first email in list
        assert result["id"] == "user_minimal123"
        assert result["email"] == "fallback@example.com"
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Smith"
        assert result["has_image"] is False

    def test_format_user_data_with_no_emails(self):
        """Test format_user_data handles users with no email addresses"""
        user = MagicMock()
        user.id = "user_no_emails"
        user.first_name = "No"
        user.last_name = "Email"
        user.has_image = False
        user.image_url = None
        user.created_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        user.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        user.email_addresses = []  # No email addresses
        user.primary_email_address_id = None

        result = ClerkDataFormatter.format_user_data(user)

        # Should handle gracefully with None email
        assert result["id"] == "user_no_emails"
        assert result["email"] is None
        assert result["first_name"] == "No"
        assert result["last_name"] == "Email"
