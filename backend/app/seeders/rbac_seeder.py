from datetime import datetime

from sqlmodel import Session, select

from app.models.rbac import Role
from app.seeders.base_seeder import BaseSeeder


class RBACSeeder(BaseSeeder):
    @staticmethod
    def get_data() -> list[dict]:
        """Get the default roles data for seeding."""
        return [
            {
                "name": "app_owner",
                "display_name": "Application Owner",
                "description": "Full application access - bypasses all restrictions",
                "permissions": ["*"],
            },
            {
                "name": "platform_admin",
                "display_name": "Platform Administrator",
                "description": "Administrative access to user management and analytics",
                "permissions": [
                    "users:*",
                    "analytics:*",
                    "webhook:*",
                    "admin:*",
                    "settings:*",
                ],
            },
            {
                "name": "support_admin",
                "display_name": "Support Administrator",
                "description": "Support staff with user management and ticket access",
                "permissions": [
                    "users:read",
                    "users:update",
                    "tickets:*",
                    "support:*",
                ],
            },
            {
                "name": "content_moderator",
                "display_name": "Content Moderator",
                "description": "Content moderation and user management capabilities",
                "permissions": [
                    "content:*",
                    "users:read",
                    "users:ban",
                    "users:suspend",
                    "moderation:*",
                ],
            },
            {
                "name": "regular_user",
                "display_name": "Regular User",
                "description": "Standard user with basic profile and content access",
                "permissions": [
                    "profile:read",
                    "profile:write",
                    "content:read",
                    "content:create",
                    "messages:*",
                ],
            },
        ]

    @staticmethod
    def seed(session: Session, force_update: bool = False) -> dict[str, str]:
        """Seed roles into the database."""
        default_roles = RBACSeeder.get_data()
        results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

        for role_data in default_roles:
            try:
                existing_role = session.exec(
                    select(Role).where(Role.name == role_data["name"])
                ).first()

                if existing_role:
                    if force_update:
                        existing_role.display_name = role_data["display_name"]
                        existing_role.description = role_data["description"]
                        existing_role.permissions = role_data["permissions"]
                        existing_role.updated_at = datetime.now()
                        session.add(existing_role)
                        results["updated"] += 1
                    else:
                        results["skipped"] += 1
                        continue
                else:
                    new_role = Role(
                        name=role_data["name"],
                        display_name=role_data["display_name"],
                        description=role_data["description"],
                        permissions=role_data["permissions"],
                    )
                    session.add(new_role)
                    results["created"] += 1

            except Exception as e:
                results["errors"].append(
                    f"Error with role '{role_data['name']}': {str(e)}"
                )
                continue

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            results["errors"].append(f"Failed to commit changes: {str(e)}")

        return results

    @staticmethod
    def create_custom_role(
        session: Session,
        name: str,
        permissions: list[str],
        display_name: str = None,
        description: str = None,
    ) -> Role:
        existing_role = session.exec(select(Role).where(Role.name == name)).first()

        if existing_role:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(
            name=name,
            display_name=display_name or name.replace("_", " ").title(),
            description=description,
            permissions=permissions,
        )

        session.add(role)
        session.commit()
        session.refresh(role)
        return role

    @staticmethod
    def get_summary(session: Session) -> dict:
        roles = session.exec(select(Role)).all()

        return {
            "total_roles": len(roles),
            "active_roles": len([r for r in roles if r.is_active]),
            "roles": [
                {
                    "name": role.name,
                    "display_name": role.display_name,
                    "permission_count": len(role.permissions)
                    if isinstance(role.permissions, list)
                    else 0,
                    "is_active": role.is_active,
                    "created_at": role.created_at.isoformat(),
                }
                for role in roles
            ],
        }
