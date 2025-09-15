from datetime import datetime

from sqlmodel import Session, select

from app.models.rbac import Role, UserRole


class RoleService:
    @staticmethod
    def get_role_by_name(session: Session, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name, Role.is_active)
        return session.exec(statement).first()

    @staticmethod
    def get_role_by_id(session: Session, role_id: int) -> Role | None:
        statement = select(Role).where(Role.id == role_id, Role.is_active)
        return session.exec(statement).first()

    @staticmethod
    def get_all_roles(session: Session, include_inactive: bool = False) -> list[Role]:
        statement = select(Role)
        if not include_inactive:
            statement = statement.where(Role.is_active)
        return list(session.exec(statement))

    @staticmethod
    def create_role(
        session: Session,
        name: str,
        permissions: list[str],
        display_name: str | None = None,
        description: str | None = None,
    ) -> Role:
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
        )
        session.add(role)
        session.commit()
        session.refresh(role)
        return role

    @staticmethod
    def update_role_permissions(
        session: Session, role_id: int, permissions: list[str]
    ) -> Role | None:
        role = RoleService.get_role_by_id(session, role_id)
        if not role:
            return None

        role.permissions = permissions
        role.updated_at = datetime.now()
        session.add(role)
        session.commit()
        session.refresh(role)
        return role

    @staticmethod
    def deactivate_role(session: Session, role_id: int) -> bool:
        role = RoleService.get_role_by_id(session, role_id)
        if not role:
            return False

        role.is_active = False
        role.updated_at = datetime.now()
        session.add(role)
        session.commit()
        return True


class UserRoleService:
    @staticmethod
    def assign_role_to_user(
        session: Session,
        user_id: int,
        role_id: int,
        assigned_by: int | None = None,
        expires_at: datetime | None = None,
    ) -> UserRole:
        existing = UserRoleService.get_user_role(session, user_id, role_id)
        if existing and existing.is_valid:
            return existing

        if existing:
            existing.is_active = False
            session.add(existing)

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
        )
        session.add(user_role)
        session.commit()
        session.refresh(user_role)
        return user_role

    @staticmethod
    def get_user_role(session: Session, user_id: int, role_id: int) -> UserRole | None:
        statement = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.is_active,
        )
        return session.exec(statement).first()

    @staticmethod
    def get_user_roles(session: Session, user_id: int) -> list[UserRole]:
        statement = (
            select(UserRole)
            .where(UserRole.user_id == user_id, UserRole.is_active)
            .join(Role)
            .where(Role.is_active)
        )
        return list(session.exec(statement))

    @staticmethod
    def remove_role_from_user(session: Session, user_id: int, role_id: int) -> bool:
        user_role = UserRoleService.get_user_role(session, user_id, role_id)
        if not user_role:
            return False

        user_role.is_active = False
        session.add(user_role)
        session.commit()
        return True

    @staticmethod
    def get_user_permissions(session: Session, user_id: int) -> list[str]:
        user_roles = UserRoleService.get_user_roles(session, user_id)
        permissions = set()

        for user_role in user_roles:
            if user_role.is_valid and user_role.role:
                if isinstance(user_role.role.permissions, list):
                    permissions.update(user_role.role.permissions)

        return list(permissions)

    @staticmethod
    def user_has_permission(session: Session, user_id: int, permission: str) -> bool:
        user_roles = UserRoleService.get_user_roles(session, user_id)

        for user_role in user_roles:
            if user_role.is_valid and user_role.role:
                if user_role.role.has_permission(permission):
                    return True

        return False

    @staticmethod
    def get_primary_role(session: Session, user_id: int) -> Role | None:
        statement = (
            select(UserRole)
            .where(UserRole.user_id == user_id, UserRole.is_active)
            .join(Role)
            .where(Role.is_active)
            .order_by(UserRole.assigned_at.asc())
        )
        user_role = session.exec(statement).first()
        return user_role.role if user_role else None
