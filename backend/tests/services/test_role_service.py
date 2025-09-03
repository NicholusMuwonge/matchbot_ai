"""
Tests for RoleService.

This tests the service layer (business logic), not just the model.
Similar to Ruby's service object specs.
"""

from sqlmodel import Session

from app.models.rbac import Role
from app.services.rbac_service import RoleService


class TestRoleService:
    """Test suite for RoleService."""

    def test_get_role_by_name(self, session: Session, sample_role: Role):
        """
        Test finding a role by name.

        Ruby equivalent:
        it 'finds role by name' do
            role = create(:role, name: 'admin')
            found = RoleService.find_by_name('admin')
            expect(found).to eq(role)
        end
        """
        # Act
        found_role = RoleService.get_role_by_name(session, sample_role.name)

        # Assert
        assert found_role is not None
        assert found_role.id == sample_role.id
        assert found_role.name == sample_role.name

    def test_get_role_by_name_not_found(self, session: Session):
        """Test that None is returned when role doesn't exist."""
        found_role = RoleService.get_role_by_name(session, "non_existent")

        assert found_role is None

    def test_get_role_by_name_ignores_inactive(self, session: Session):
        """Test that inactive roles are not returned."""
        # Create inactive role
        role = Role(
            name="inactive_role",
            permissions=[],
            is_active=False,
        )
        session.add(role)
        session.commit()

        # Should not find inactive role
        found_role = RoleService.get_role_by_name(session, "inactive_role")
        assert found_role is None

    def test_get_all_roles_excludes_inactive_by_default(self, session: Session):
        """Test that get_all_roles excludes inactive roles by default."""
        # Create mix of active and inactive roles
        active1 = Role(name="active1", permissions=[], is_active=True)
        active2 = Role(name="active2", permissions=[], is_active=True)
        inactive = Role(name="inactive", permissions=[], is_active=False)

        session.add_all([active1, active2, inactive])
        session.commit()

        # Get all roles (should exclude inactive)
        roles = RoleService.get_all_roles(session)
        role_names = [r.name for r in roles]

        assert "active1" in role_names
        assert "active2" in role_names
        assert "inactive" not in role_names

    def test_get_all_roles_includes_inactive_when_requested(self, session: Session):
        """Test that get_all_roles can include inactive roles."""
        # Create mix of active and inactive roles
        active = Role(name="active", permissions=[], is_active=True)
        inactive = Role(name="inactive", permissions=[], is_active=False)

        session.add_all([active, inactive])
        session.commit()

        # Get all roles including inactive
        roles = RoleService.get_all_roles(session, include_inactive=True)
        role_names = [r.name for r in roles]

        assert "active" in role_names
        assert "inactive" in role_names

    def test_create_role(self, session: Session):
        """
        Test creating a new role through the service.

        Ruby equivalent:
        it 'creates a role with given attributes' do
            role = RoleService.create(
                name: 'moderator',
                permissions: ['posts:edit']
            )
            expect(role).to be_persisted
            expect(role.reload.name).to eq('moderator')
        end
        """
        # Act
        role = RoleService.create_role(
            session=session,
            name="moderator",
            permissions=["posts:edit", "posts:delete"],
            display_name="Moderator",
            description="Content moderator",
        )

        # Assert
        assert role.id is not None  # Persisted
        assert role.name == "moderator"
        assert role.display_name == "Moderator"
        assert len(role.permissions) == 2
        assert "posts:edit" in role.permissions

        # Verify it's in database
        found = session.get(Role, role.id)
        assert found is not None
        assert found.name == "moderator"

    def test_update_role_permissions(self, session: Session, sample_role: Role):
        """Test updating role permissions."""
        # Arrange
        original_permissions = sample_role.permissions.copy()
        new_permissions = ["admin:read", "admin:write", "admin:delete"]

        # Act
        updated_role = RoleService.update_role_permissions(
            session, sample_role.id, new_permissions
        )

        # Assert
        assert updated_role is not None
        assert updated_role.permissions == new_permissions
        assert updated_role.permissions != original_permissions
        assert updated_role.updated_at is not None

    def test_update_role_permissions_not_found(self, session: Session):
        """Test updating permissions for non-existent role."""
        result = RoleService.update_role_permissions(
            session, 999999, ["some:permission"]
        )

        assert result is None

    def test_deactivate_role(self, session: Session, sample_role: Role):
        """
        Test deactivating a role.

        Ruby equivalent:
        it 'soft deletes the role' do
            role = create(:role, active: true)
            RoleService.deactivate(role.id)
            expect(role.reload.active?).to be false
        end
        """
        # Ensure role starts active
        assert sample_role.is_active is True

        # Act
        success = RoleService.deactivate_role(session, sample_role.id)

        # Assert
        assert success is True

        # Refresh from database
        session.refresh(sample_role)
        assert sample_role.is_active is False
        assert sample_role.updated_at is not None

    def test_deactivate_role_not_found(self, session: Session):
        """Test deactivating non-existent role."""
        success = RoleService.deactivate_role(session, 999999)

        assert success is False


class TestRoleServiceIntegration:
    """
    Integration tests that test multiple service methods together.
    Similar to Ruby's feature specs or integration tests.
    """

    def test_role_lifecycle(self, session: Session):
        """Test complete role lifecycle: create, update, deactivate."""
        # Create
        role = RoleService.create_role(
            session,
            name="lifecycle_test",
            permissions=["read"],
        )
        assert role.id is not None

        # Update
        updated = RoleService.update_role_permissions(
            session,
            role.id,
            ["read", "write", "delete"],
        )
        assert len(updated.permissions) == 3

        # Deactivate
        success = RoleService.deactivate_role(session, role.id)
        assert success is True

        # Should not find deactivated role
        found = RoleService.get_role_by_name(session, "lifecycle_test")
        assert found is None

        # But can find with include_inactive
        all_roles = RoleService.get_all_roles(session, include_inactive=True)
        role_names = [r.name for r in all_roles]
        assert "lifecycle_test" in role_names
