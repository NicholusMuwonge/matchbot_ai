"""
Tests for RoleAssignmentService - Refactored Version

This test suite demonstrates:
- Factory patterns for dynamic test data (addressing your fixture concerns)
- Nested class organization (Python's equivalent to Ruby's describe/context)
- Parameterized tests for multiple scenarios
- Proper separation of concerns
"""

import os
from typing import Dict, Any
from unittest.mock import patch

import pytest
from sqlmodel import Session

from app.models.rbac import Role, UserRole
from app.models.user import User
from app.services.role_assignment_service import RoleAssignmentService


class UserDataFactory:
    """Factory for creating test user data - addressing your fixture concerns."""
    
    @staticmethod
    def create_clerk_user_data(
        clerk_id: str = "user_123abc",
        primary_email: str = "john@example.com", 
        primary_verified: bool = True,
        additional_emails: list = None
    ) -> Dict[str, Any]:
        """Create clerk user data with flexible parameters."""
        base_data = {
            "id": clerk_id,
            "first_name": "John",
            "last_name": "Doe",
            "email_addresses": [
                {
                    "email_address": primary_email,
                    "primary": True,
                    "id": "email_1",
                    "verification": {
                        "status": "verified" if primary_verified else "unverified"
                    }
                }
            ]
        }
        
        if additional_emails:
            for i, email_data in enumerate(additional_emails, start=2):
                base_data["email_addresses"].append({
                    "email_address": email_data["email"],
                    "primary": email_data.get("primary", False),
                    "id": f"email_{i}",
                    "verification": {
                        "status": "verified" if email_data.get("verified", False) else "unverified"
                    }
                })
        
        return base_data


class TestRoleAssignmentService:
    """Test suite for RoleAssignmentService - using nested classes for organization."""
    
    @pytest.fixture
    def service(self, session: Session) -> RoleAssignmentService:
        """Create service instance for testing."""
        return RoleAssignmentService(session)

    class TestGetPrimaryEmail:
        """Tests for email extraction - organized like Ruby's describe block."""
        
        def test_primary_verified_email(self, service: RoleAssignmentService):
            """Should return primary verified email when available."""
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="john@example.com",
                primary_verified=True
            )
            email = service.get_primary_email(user_data)
            assert email == "john@example.com"
        
        def test_no_primary_email(self, service: RoleAssignmentService):
            """Should return first verified email when no primary is set."""
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="first@example.com",
                primary_verified=True,
                additional_emails=[
                    {"email": "second@example.com", "primary": False, "verified": True}
                ]
            )
            user_data["email_addresses"][0]["primary"] = False
            
            email = service.get_primary_email(user_data)
            assert email == "first@example.com"
        
        def test_unverified_primary_email(self, service: RoleAssignmentService):
            """Should return first verified email when primary is unverified."""
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="primary@example.com",
                primary_verified=False,
                additional_emails=[
                    {"email": "verified@example.com", "primary": False, "verified": True}
                ]
            )
            
            email = service.get_primary_email(user_data)
            assert email == "verified@example.com"
        
        def test_no_verified_emails(self, service: RoleAssignmentService):
            """Should return None when no emails are verified."""
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="unverified@example.com",
                primary_verified=False
            )
            
            email = service.get_primary_email(user_data)
            assert email is None
        
        def test_empty_email_addresses(self, service: RoleAssignmentService):
            """Should handle empty email addresses gracefully."""
            user_data = {"email_addresses": []}
            email = service.get_primary_email(user_data)
            assert email is None
    
    class TestDetermineUserRole:
        """Tests for role determination logic - context-like organization."""
        
        def test_platform_admin_role_assignment(self, session: Session):
            """Should assign platform_admin role to @matchbot.ai emails."""
            admin_role = Role(name="platform_admin", permissions=["users:*", "admin:*"])
            session.add(admin_role)
            session.commit()
            
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="admin@matchbot.ai",
                primary_verified=True
            )
            
            role = service.determine_user_role(user_data)
            
            assert role is not None
            assert role.name == "platform_admin"
        
        @patch.dict(os.environ, {'APP_OWNER_EMAIL': 'owner@example.com'})
        def test_app_owner_role_assignment(self, session: Session):
            """Should assign app_owner role to configured email."""
            owner_role = Role(name="app_owner", permissions=["*"])
            session.add(owner_role)
            session.commit()
            
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="owner@example.com",
                primary_verified=True
            )
            
            role = service.determine_user_role(user_data)
            
            assert role is not None
            assert role.name == "app_owner"
        
        def test_regular_user_role_assignment(self, session: Session):
            """Should assign regular_user role to normal emails."""
            regular_role = Role(name="regular_user", permissions=["profile:read"])
            session.add(regular_role)
            session.commit()
            
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="user@example.com",
                primary_verified=True
            )
            
            role = service.determine_user_role(user_data)
            
            assert role is not None
            assert role.name == "regular_user"
        
        def test_no_verified_email_returns_none(self, session: Session):
            """Should return None when no verified email exists."""
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="unverified@example.com",
                primary_verified=False
            )
            
            role = service.determine_user_role(user_data)
            assert role is None
    
    class TestAssignInitialRole:
        """Tests for initial role assignment - another context-like block."""
        
        @pytest.mark.asyncio
        async def test_successful_role_assignment(self, session: Session):
            """Should successfully assign role to user."""
            user = User(
                email="test@example.com",
                full_name="Test User",
                clerk_user_id="user_test123"
            )
            session.add(user)
            
            regular_role = Role(name="regular_user", permissions=["profile:read"])
            session.add(regular_role)
            session.commit()
            
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="test@example.com",
                primary_verified=True
            )
            
            result = await service.assign_initial_role(user, user_data)
            
            assert result["success"] is True
            assert result["role_assigned"] == "regular_user"
            assert result["user_id"] == user.id
            
            from sqlmodel import select
            user_role = session.exec(
                select(UserRole).where(UserRole.user_id == user.id)
            ).first()
            assert user_role is not None
            assert user_role.role_id == regular_role.id
        
        @pytest.mark.asyncio
        async def test_no_role_found_failure(self, session: Session):
            """Should handle case where no appropriate role exists."""
            user = User(
                email="test@example.com",
                full_name="Test User",
                clerk_user_id="user_test123"
            )
            session.add(user)
            session.commit()
            
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="test@example.com",
                primary_verified=True
            )
            
            result = await service.assign_initial_role(user, user_data)
            
            assert result["success"] is False
            assert "no appropriate role found" in result["message"].lower()
            assert result["user_id"] == user.id
        
        @pytest.mark.asyncio
        async def test_unverified_email_failure(self, session: Session):
            """Should fail when user has no verified email."""
            user = User(
                email="test@example.com",
                full_name="Test User",
                clerk_user_id="user_test123"
            )
            session.add(user)
            
            regular_role = Role(name="regular_user", permissions=["profile:read"])
            session.add(regular_role)
            session.commit()
            
            service = RoleAssignmentService(session)
            user_data = UserDataFactory.create_clerk_user_data(
                primary_email="test@example.com",
                primary_verified=False  # Unverified email
            )
            
            result = await service.assign_initial_role(user, user_data)
            
            assert result["success"] is False
            assert result["user_id"] == user.id


class TestRoleAssignmentIntegration:
    """Integration tests demonstrating parameterized testing."""
    
    @pytest.mark.parametrize("email,expected_role", [
        ("admin@matchbot.ai", "platform_admin"),
        ("user@example.com", "regular_user"),
        ("support@company.com", "regular_user"),
    ])
    def test_role_assignment_by_email_domain(self, session: Session, email: str, expected_role: str):
        """Test role assignment for various email domains - parameterized test."""
        roles = [
            Role(name="platform_admin", permissions=["users:*", "admin:*"]),
            Role(name="regular_user", permissions=["profile:read"]),
        ]
        for role in roles:
            session.add(role)
        session.commit()
        
        service = RoleAssignmentService(session)
        user_data = UserDataFactory.create_clerk_user_data(
            primary_email=email,
            primary_verified=True
        )
        
        role = service.determine_user_role(user_data)

        assert role is not None
        assert role.name == expected_role

