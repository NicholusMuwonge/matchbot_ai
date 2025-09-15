"""
Tests for RBAC models (Role and UserRole).

Python Testing Concepts for Ruby Developers:
- `def test_*` functions are like Ruby's `it` blocks
- `assert` statements are like Ruby's `expect().to`
- `pytest.raises` is like Ruby's `expect { }.to raise_error`
- Fixtures are like `let` statements or `before` blocks
"""

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from app.models.rbac import Role, UserRole


class TestRoleModel:
    """
    Test suite for Role model.
    Similar to Ruby's `describe Role do ... end`
    """

    def test_role_creation(self, session: Session):
        """
        Test basic role creation.

        Ruby equivalent:
        it 'creates a role with valid attributes' do
            role = Role.create!(name: 'admin', ...)
            expect(role).to be_persisted
            expect(role.name).to eq('admin')
        end
        """
        # Arrange (Given)
        role_data = {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Admin role",
            "permissions": ["users:read", "users:write", "users:delete"],
        }

        # Act (When)
        role = Role(**role_data)
        session.add(role)
        session.commit()

        # Assert (Then)
        assert role.id is not None  # Like: expect(role.id).not_to be_nil
        assert role.name == "admin"  # Like: expect(role.name).to eq('admin')
        assert role.display_name == "Administrator"
        assert len(role.permissions) == 3
        assert "users:read" in role.permissions

    def test_role_unique_name_constraint(self, session: Session):
        """
        Test that role names must be unique.

        Ruby equivalent:
        it 'enforces unique role names' do
            create(:role, name: 'admin')
            expect { create(:role, name: 'admin') }.to raise_error(ActiveRecord::RecordInvalid)
        end
        """
        # Create first role
        role1 = Role(name="unique_role", permissions=[])
        session.add(role1)
        session.commit()

        # Try to create duplicate - should fail
        role2 = Role(name="unique_role", permissions=[])
        session.add(role2)

        # In Python, we use pytest.raises as context manager
        # This is like Ruby's expect { }.to raise_error
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            session.commit()

    def test_has_permission_with_exact_match(self, sample_role: Role):
        """
        Test permission checking with exact match.

        Ruby equivalent:
        it 'returns true for exact permission match' do
            role = create(:role, permissions: ['users:read'])
            expect(role.has_permission?('users:read')).to be true
        end
        """
        # sample_role has ["users:read", "users:write"]
        assert sample_role.has_permission("users:read") is True
        assert sample_role.has_permission("users:write") is True
        assert sample_role.has_permission("users:delete") is False

    def test_has_permission_with_wildcard(self, app_owner_role: Role):
        """
        Test permission checking with wildcard (*).

        Ruby equivalent:
        it 'grants all permissions with wildcard' do
            role = create(:role, permissions: ['*'])
            expect(role.has_permission?('anything')).to be true
        end
        """
        # app_owner_role has ["*"]
        assert app_owner_role.has_permission("users:read") is True
        assert app_owner_role.has_permission("admin:delete") is True
        assert app_owner_role.has_permission("anything:at:all") is True

    def test_has_permission_with_resource_wildcard(self, session: Session):
        """
        Test permission checking with resource wildcard (users:*).
        """
        role = Role(
            name="user_admin",
            permissions=["users:*", "posts:read"],
        )
        session.add(role)
        session.commit()

        # Should match any users: permission
        assert role.has_permission("users:read") is True
        assert role.has_permission("users:write") is True
        assert role.has_permission("users:delete") is True

        # Should not match other resources
        assert role.has_permission("posts:write") is False
        assert role.has_permission("admin:read") is False

    def test_add_permission(self, sample_role: Role):
        """
        Test adding a permission to a role.

        Ruby equivalent:
        it 'adds a new permission' do
            role.add_permission('users:delete')
            expect(role.permissions).to include('users:delete')
        end
        """
        initial_count = len(sample_role.permissions)

        sample_role.add_permission("users:delete")

        assert len(sample_role.permissions) == initial_count + 1
        assert "users:delete" in sample_role.permissions
        assert sample_role.updated_at is not None

    def test_add_duplicate_permission(self, sample_role: Role):
        """Test that duplicate permissions are not added."""
        initial_count = len(sample_role.permissions)

        # Try to add existing permission
        sample_role.add_permission("users:read")

        # Should not add duplicate
        assert len(sample_role.permissions) == initial_count

    def test_remove_permission(self, sample_role: Role):
        """Test removing a permission from a role."""
        sample_role.remove_permission("users:read")

        assert "users:read" not in sample_role.permissions
        assert "users:write" in sample_role.permissions  # Other permission remains
        assert sample_role.updated_at is not None


class TestUserRoleModel:
    """
    Test suite for UserRole model.
    Similar to Ruby's `describe UserRole do ... end`
    """

    def test_user_role_creation(self, session: Session, sample_role: Role, sample_user):
        """Test creating a user-role association."""
        user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
        )
        session.add(user_role)
        session.commit()

        assert user_role.id is not None
        assert user_role.user_id == sample_user.id
        assert user_role.role_id == sample_role.id
        assert user_role.is_active is True
        assert user_role.assigned_at is not None

    def test_is_expired_with_no_expiration(
        self, session: Session, sample_role: Role, sample_user
    ):
        """
        Test that role without expiration is not expired.

        Ruby equivalent:
        it 'is not expired when expires_at is nil' do
            user_role = create(:user_role, expires_at: nil)
            expect(user_role.expired?).to be false
        end
        """
        user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
            expires_at=None,  # No expiration
        )

        assert user_role.is_expired is False
        assert user_role.is_valid is True

    def test_is_expired_with_future_expiration(
        self, session: Session, sample_role: Role, sample_user
    ):
        """Test that role with future expiration is not expired."""
        future_date = datetime.now() + timedelta(days=30)

        user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
            expires_at=future_date,
        )

        assert user_role.is_expired is False
        assert user_role.is_valid is True

    def test_is_expired_with_past_expiration(
        self, session: Session, sample_role: Role, sample_user
    ):
        """Test that role with past expiration is expired."""
        past_date = datetime.now() - timedelta(days=1)

        user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
            expires_at=past_date,
        )

        assert user_role.is_expired is True
        assert user_role.is_valid is False  # Not valid if expired

    def test_is_valid_when_inactive(
        self, session: Session, sample_role: Role, sample_user
    ):
        """Test that inactive role is not valid."""
        user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
            is_active=False,
        )

        assert user_role.is_valid is False

    def test_role_relationship(self, session: Session, sample_role: Role, sample_user):
        """
        Test the relationship between UserRole and Role.

        Ruby equivalent:
        it 'belongs to a role' do
            user_role = create(:user_role, role: role)
            expect(user_role.role).to eq(role)
        end
        """
        user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
        )
        session.add(user_role)
        session.commit()
        session.refresh(user_role)

        # Test relationship loading
        assert user_role.role is not None
        assert user_role.role.id == sample_role.id
        assert user_role.role.name == sample_role.name


# Parameterized tests - similar to Ruby's shared examples
@pytest.mark.parametrize(
    "permission,resource,expected",
    [
        ("users:read", "users:*", True),
        ("users:write", "users:*", True),
        ("posts:read", "users:*", False),
        ("users:read", "*", True),
        ("anything", "*", True),
    ],
)
def test_wildcard_permission_matching(permission: str, resource: str, expected: bool):
    """
    Parameterized test for wildcard matching.

    Ruby equivalent of shared examples:
    shared_examples 'wildcard matching' do |permission, resource, expected|
        it "matches #{permission} against #{resource}" do
            role = create(:role, permissions: [resource])
            expect(role.has_permission?(permission)).to eq(expected)
        end
    end
    """
    role = Role(name="test", permissions=[resource])
    assert role.has_permission(permission) is expected
