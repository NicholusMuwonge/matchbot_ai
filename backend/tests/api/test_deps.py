import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from sqlmodel import Session, select

from app.api.deps import (
    get_current_user_session, 
    require_role, 
    require_permission,
    AdminUser,
    AppOwnerUser,
    PlatformAdminUser
)
from app.models import User
from app.services.clerk_auth import ClerkAuthenticationError


class TestGetCurrentUserSession:
    """Test the main session authentication function"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request object"""
        request = Mock(spec=Request)
        return request
    
    @pytest.fixture
    def mock_session(self):
        """Mock SQLModel Session"""
        session = Mock(spec=Session)
        return session
    
    @pytest.fixture
    def mock_user(self):
        """Mock User object"""
        user = Mock(spec=User)
        user.clerk_user_id = "clerk_123"
        user.is_active = True
        user.id = "user_123"
        return user

    @patch('app.api.deps.ClerkService')
    @patch('app.api.deps.UserSyncService')
    def test_successful_authentication(self, mock_sync_service, mock_clerk_service, mock_request, mock_session, mock_user):
        """Test successful user authentication flow"""
        # Setup mocks
        mock_clerk_service.return_value.authenticate_session.return_value = {
            "user_id": "clerk_123"
        }
        mock_session.exec.return_value.first.return_value = mock_user
        
        # Call function
        result = get_current_user_session(mock_request, mock_session)
        
        # Assertions
        assert result == mock_user
        mock_clerk_service.return_value.authenticate_session.assert_called_once_with(mock_request)
        mock_session.exec.assert_called_once()

    @patch('app.api.deps.ClerkService')
    def test_authentication_no_user_id(self, mock_clerk_service, mock_request, mock_session):
        """Test authentication failure when no user ID in auth data"""
        # Setup mock to return empty auth data
        mock_clerk_service.return_value.authenticate_session.return_value = {}
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_session(mock_request, mock_session)
        
        assert exc_info.value.status_code == 401
        assert "No user ID in authenticated request" in str(exc_info.value.detail)

    @patch('app.api.deps.ClerkService')
    @patch('app.api.deps.UserSyncService')
    def test_user_not_found_with_sync(self, mock_sync_service, mock_clerk_service, mock_request, mock_session, mock_user):
        """Test user sync when user not found in database"""
        # Setup mocks
        mock_clerk_service.return_value.authenticate_session.return_value = {
            "user_id": "clerk_123"
        }
        # First call returns None (user not found), second call returns mock user after sync
        mock_session.exec.return_value.first.return_value = None
        mock_session.get.return_value = mock_user
        mock_sync_service.return_value.fetch_and_sync_user.return_value = {
            "user_id": "user_123"
        }
        
        # Call function
        result = get_current_user_session(mock_request, mock_session)
        
        # Assertions
        assert result == mock_user
        mock_sync_service.return_value.fetch_and_sync_user.assert_called_once_with("clerk_123")

    @patch('app.api.deps.ClerkService')
    def test_inactive_user(self, mock_clerk_service, mock_request, mock_session, mock_user):
        """Test authentication failure with inactive user"""
        # Setup mocks
        mock_clerk_service.return_value.authenticate_session.return_value = {
            "user_id": "clerk_123"
        }
        mock_user.is_active = False  # Set user as inactive
        mock_session.exec.return_value.first.return_value = mock_user
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_session(mock_request, mock_session)
        
        assert exc_info.value.status_code == 400
        assert "User account is inactive" in str(exc_info.value.detail)

    @patch('app.api.deps.ClerkService')
    def test_clerk_authentication_error(self, mock_clerk_service, mock_request, mock_session):
        """Test handling of Clerk authentication errors"""
        # Setup mock to raise ClerkAuthenticationError
        mock_clerk_service.return_value.authenticate_session.side_effect = ClerkAuthenticationError("Invalid token")
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_session(mock_request, mock_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)


class TestRequireRole:
    """Test the require_role factory function"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock User with ID"""
        user = Mock(spec=User)
        user.id = "user_123"
        return user
    
    @pytest.fixture  
    def mock_session(self):
        """Mock SQLModel Session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user_role(self):
        """Mock UserRole object"""
        user_role = Mock()
        user_role.role_id = "role_123"
        return user_role
    
    @pytest.fixture
    def mock_role(self):
        """Mock Role object"""
        role = Mock()
        role.id = "role_123"
        role.name = "platform_admin"
        role.permissions = ["users:read", "users:write"]
        return role

    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService')
    def test_single_role_success(self, mock_role_service, mock_user_role_service, mock_user, mock_session, mock_user_role, mock_role):
        """Test successful role check with single role"""
        # Setup mocks
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Create dependency function
        dependency_func = require_role("platform_admin")
        
        # Call dependency
        result = dependency_func(mock_user, mock_session)
        
        # Assertions
        assert result == mock_user
        mock_user_role_service.return_value.get_user_roles.assert_called_once_with(mock_session, mock_user.id)
        mock_role_service.return_value.get_role.assert_called_once_with(mock_session, mock_user_role.role_id)

    @patch('app.api.deps.UserRoleService') 
    @patch('app.api.deps.RoleService')
    def test_multiple_roles_success(self, mock_role_service, mock_user_role_service, mock_user, mock_session, mock_user_role, mock_role):
        """Test successful role check with multiple allowed roles"""
        # Setup mocks
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Create dependency function with multiple roles
        dependency_func = require_role(["platform_admin", "app_owner"])
        
        # Call dependency
        result = dependency_func(mock_user, mock_session)
        
        # Assertions
        assert result == mock_user

    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService') 
    def test_role_check_failure(self, mock_role_service, mock_user_role_service, mock_user, mock_session, mock_user_role):
        """Test role check failure when user doesn't have required role"""
        # Setup mocks - user has different role
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        mock_role = Mock()
        mock_role.name = "regular_user"  # Different role than required
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Create dependency function
        dependency_func = require_role("platform_admin")
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            dependency_func(mock_user, mock_session)
        
        assert exc_info.value.status_code == 403
        assert "role required" in str(exc_info.value.detail).lower()

    @patch('app.api.deps.UserRoleService')
    def test_no_roles_assigned(self, mock_user_role_service, mock_user, mock_session):
        """Test role check failure when user has no roles"""
        # Setup mock - user has no roles
        mock_user_role_service.return_value.get_user_roles.return_value = []
        
        # Create dependency function
        dependency_func = require_role("platform_admin")
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            dependency_func(mock_user, mock_session)
        
        assert exc_info.value.status_code == 403


class TestRequirePermission:
    """Test the require_permission factory function"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock User with ID"""
        user = Mock(spec=User)
        user.id = "user_123"
        return user
    
    @pytest.fixture
    def mock_session(self):
        """Mock SQLModel Session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user_role(self):
        """Mock UserRole object"""
        user_role = Mock()
        user_role.role_id = "role_123"
        return user_role
    
    @pytest.fixture
    def mock_role(self):
        """Mock Role object with permissions"""
        role = Mock()
        role.id = "role_123"
        role.permissions = ["users:read", "users:write", "items:read"]
        return role

    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService')
    def test_permission_success(self, mock_role_service, mock_user_role_service, mock_user, mock_session, mock_user_role, mock_role):
        """Test successful permission check"""
        # Setup mocks
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Create dependency function
        dependency_func = require_permission("users:read")
        
        # Call dependency
        result = dependency_func(mock_user, mock_session)
        
        # Assertions
        assert result == mock_user

    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService')
    def test_wildcard_permission(self, mock_role_service, mock_user_role_service, mock_user, mock_session, mock_user_role):
        """Test wildcard permission (*) grants all access"""
        # Setup mocks - role has wildcard permission
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        mock_role = Mock()
        mock_role.permissions = ["*"]  # Wildcard permission
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Create dependency function
        dependency_func = require_permission("any:permission")
        
        # Call dependency
        result = dependency_func(mock_user, mock_session)
        
        # Assertions
        assert result == mock_user

    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService')
    def test_permission_failure(self, mock_role_service, mock_user_role_service, mock_user, mock_session, mock_user_role, mock_role):
        """Test permission check failure"""
        # Setup mocks - user doesn't have required permission
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Create dependency function for permission user doesn't have
        dependency_func = require_permission("admin:delete")
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            dependency_func(mock_user, mock_session)
        
        assert exc_info.value.status_code == 403
        assert "Permission 'admin:delete' required" in str(exc_info.value.detail)


class TestTypeAliases:
    """Test the pre-defined type aliases"""
    
    def test_admin_user_alias(self):
        """Test AdminUser type alias"""
        # AdminUser should be require_role(["app_owner", "platform_admin"])
        assert AdminUser is not None
        # This is a type alias, so we can't test much more than it exists
    
    def test_app_owner_user_alias(self):
        """Test AppOwnerUser type alias"""
        # AppOwnerUser should be require_role("app_owner")
        assert AppOwnerUser is not None
    
    def test_platform_admin_user_alias(self):
        """Test PlatformAdminUser type alias"""
        # PlatformAdminUser should be require_role("platform_admin")
        assert PlatformAdminUser is not None


class TestDependencyIntegration:
    """Integration tests for dependency system"""
    
    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService')
    def test_admin_user_with_app_owner_role(self, mock_role_service, mock_user_role_service):
        """Test that AdminUser accepts app_owner role"""
        # Setup mocks
        mock_user = Mock(spec=User)
        mock_user.id = "user_123"
        mock_session = Mock(spec=Session)
        
        mock_user_role = Mock()
        mock_user_role.role_id = "role_123"
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        
        mock_role = Mock()
        mock_role.name = "app_owner"
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Test AdminUser dependency (should accept app_owner)
        result = AdminUser(mock_user, mock_session)
        
        assert result == mock_user

    @patch('app.api.deps.UserRoleService')
    @patch('app.api.deps.RoleService')
    def test_admin_user_with_platform_admin_role(self, mock_role_service, mock_user_role_service):
        """Test that AdminUser accepts platform_admin role"""
        # Setup mocks
        mock_user = Mock(spec=User)
        mock_user.id = "user_123"
        mock_session = Mock(spec=Session)
        
        mock_user_role = Mock()
        mock_user_role.role_id = "role_123"
        mock_user_role_service.return_value.get_user_roles.return_value = [mock_user_role]
        
        mock_role = Mock()
        mock_role.name = "platform_admin"
        mock_role_service.return_value.get_role.return_value = mock_role
        
        # Test AdminUser dependency (should accept platform_admin)
        result = AdminUser(mock_user, mock_session)
        
        assert result == mock_user