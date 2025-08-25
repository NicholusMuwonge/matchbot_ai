"""
Tests for formatters module
"""

import pytest

from app.core.formatters import ClerkDataFormatter
from app.tests.fixtures.clerk_fixtures import create_clerk_user_mock


class TestClerkDataFormatter:
    """Test ClerkDataFormatter functionality"""

    @pytest.fixture
    def sample_clerk_user(self):
        """Create a default sample Clerk SDK User object for testing"""
        return create_clerk_user_mock()

    def test_format_user_data(self, sample_clerk_user):
        """Test format_user_data returns correctly formatted user data"""
        result = ClerkDataFormatter.format_user_data(sample_clerk_user)

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

        assert result["id"] == sample_clerk_user.id
        assert result["email"] == "test@example.com"
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
        user = create_clerk_user_mock(
            user_id="user_minimal123",
            first_name="Jane",
            last_name="Smith",
            emails=[{"id": "idn_different_email", "email": "fallback@example.com"}],
            primary_email_id="idn_nonexistent",  # Doesn't match any email
        )

        result = ClerkDataFormatter.format_user_data(user)

        # Should fallback to first email in list
        assert result["id"] == "user_minimal123"
        assert result["email"] == "fallback@example.com"
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Smith"
        assert result["has_image"] is False

    def test_format_user_data_with_no_emails(self):
        """Test format_user_data handles users with no email addresses"""
        user = create_clerk_user_mock(
            user_id="user_no_emails",
            first_name="No",
            last_name="Email",
            emails=[],  # Empty emails list
            primary_email_id=None,
        )

        result = ClerkDataFormatter.format_user_data(user)

        # Should handle gracefully with None email
        assert result["id"] == "user_no_emails"
        assert result["email"] is None
        assert result["first_name"] == "No"
        assert result["last_name"] == "Email"
