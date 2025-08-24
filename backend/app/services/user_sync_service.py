from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.core.db import engine
from app.models import User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService


class UserSyncError(Exception):
    pass


class UserSyncService:
    def __init__(self):
        self.clerk_service = ClerkService()

    async def sync_user_from_clerk(self, clerk_data: dict[str, Any]) -> dict[str, Any]:
        try:
            clerk_user_id = clerk_data.get("id")
            if not clerk_user_id:
                raise UserSyncError("Clerk user ID is required")

            with Session(engine) as session:
                existing_user = self.find_user_by_clerk_id(session, clerk_user_id)

                if existing_user:
                    updated_user = self._update_user_from_clerk_data(
                        session, existing_user, clerk_data
                    )
                    session.commit()
                    session.refresh(updated_user)

                    return {
                        "status": "updated",
                        "user_id": str(updated_user.id),
                        "clerk_user_id": clerk_user_id,
                        "action": "user_updated",
                    }
                else:
                    new_user = self._create_user_from_clerk_data(session, clerk_data)
                    session.add(new_user)
                    session.commit()
                    session.refresh(new_user)

                    return {
                        "status": "created",
                        "user_id": str(new_user.id),
                        "clerk_user_id": clerk_user_id,
                        "action": "user_created",
                    }

        except Exception as e:
            raise UserSyncError(f"Failed to sync user from Clerk: {str(e)}")

    def find_user_by_clerk_id(self, session: Session, clerk_id: str) -> User | None:
        """Find local user by Clerk ID"""
        try:
            statement = select(User).where(User.clerk_user_id == clerk_id)
            result = session.exec(statement)
            return result.first()
        except Exception as e:
            raise UserSyncError(f"Failed to find user by Clerk ID: {str(e)}")

    def find_user_by_email(self, session: Session, email: str) -> User | None:
        try:
            statement = select(User).where(User.email == email)
            result = session.exec(statement)
            return result.first()
        except Exception as e:
            raise UserSyncError(f"Failed to find user by email: {str(e)}")

    def _create_user_from_clerk_data(
        self, session: Session, clerk_data: dict[str, Any]
    ) -> User:
        try:
            email_addresses = clerk_data.get("email_addresses", [])
            primary_email = None

            for email_obj in email_addresses:
                if email_obj.get("verification", {}).get("status") == "verified":
                    primary_email = email_obj.get("email_address")
                    break

            if not primary_email and email_addresses:
                primary_email = email_addresses[0].get("email_address")

            if not primary_email:
                raise UserSyncError("No email address found in Clerk data")

            existing_user = self.find_user_by_email(session, primary_email)
            if existing_user:
                existing_user.clerk_user_id = clerk_data.get("id")
                existing_user.is_synced = True
                existing_user.auth_provider = "clerk"
                self._update_user_fields_from_clerk(existing_user, clerk_data)
                return existing_user
            user = User(
                clerk_user_id=clerk_data.get("id"),
                email=primary_email,
                first_name=clerk_data.get("first_name"),
                last_name=clerk_data.get("last_name"),
                full_name=f"{clerk_data.get('first_name', '')} {clerk_data.get('last_name', '')}".strip(),
                profile_image_url=clerk_data.get("image_url"),
                auth_provider="clerk",
                is_synced=True,
                email_verified=any(
                    email.get("verification", {}).get("status") == "verified"
                    for email in email_addresses
                ),
                created_at=datetime.utcnow(),
                hashed_password="clerk_managed",
            )

            return user

        except Exception as e:
            raise UserSyncError(f"Failed to create user from Clerk data: {str(e)}")

    def _update_user_from_clerk_data(
        self, session: Session, user: User, clerk_data: dict[str, Any]
    ) -> User:
        """Update existing user with fresh Clerk data"""
        try:
            self._update_user_fields_from_clerk(user, clerk_data)
            user.is_synced = True
            user.auth_provider = "clerk"

            return user

        except Exception as e:
            raise UserSyncError(f"Failed to update user from Clerk data: {str(e)}")

    def _update_user_fields_from_clerk(
        self, user: User, clerk_data: dict[str, Any]
    ) -> None:
        user.first_name = clerk_data.get("first_name")
        user.last_name = clerk_data.get("last_name")
        user.full_name = f"{clerk_data.get('first_name', '')} {clerk_data.get('last_name', '')}".strip()
        user.profile_image_url = clerk_data.get("image_url")
        email_addresses = clerk_data.get("email_addresses", [])
        user.email_verified = any(
            email.get("verification", {}).get("status") == "verified"
            for email in email_addresses
        )
        for email_obj in email_addresses:
            if email_obj.get("verification", {}).get("status") == "verified":
                new_email = email_obj.get("email_address")
                if new_email and new_email != user.email:
                    user.email = new_email
                break

    async def fetch_and_sync_user(self, clerk_user_id: str) -> dict[str, Any]:
        try:
            clerk_data = self.clerk_service.get_user(clerk_user_id)

            if not clerk_data:
                raise UserSyncError(f"User not found in Clerk: {clerk_user_id}")
            return await self.sync_user_from_clerk(clerk_data)

        except ClerkAuthenticationError as e:
            raise UserSyncError(f"Clerk API error: {str(e)}")
        except Exception as e:
            raise UserSyncError(f"Failed to fetch and sync user: {str(e)}")

    async def sync_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Find user by email in Clerk and sync to local database"""
        try:
            users_response = self.clerk_service.list_users(email=email, limit=1)
            users = users_response.get("data", [])

            if not users:
                return None
            clerk_data = users[0]
            return await self.sync_user_from_clerk(clerk_data)

        except ClerkAuthenticationError as e:
            raise UserSyncError(f"Clerk API error: {str(e)}")
        except Exception as e:
            raise UserSyncError(f"Failed to sync user by email: {str(e)}")

    def delete_user_by_clerk_id(self, clerk_user_id: str) -> bool:
        try:
            with Session(engine) as session:
                user = self.find_user_by_clerk_id(session, clerk_user_id)

                if user:
                    user.is_active = False
                    user.is_synced = False
                    session.commit()
                    return True

                return False

        except Exception as e:
            raise UserSyncError(f"Failed to delete user: {str(e)}")

    def get_sync_stats(self) -> dict[str, int]:
        try:
            with Session(engine) as session:
                total_users = session.exec(select(User)).all()

                synced_users = len(
                    [
                        u
                        for u in total_users
                        if u.is_synced and u.auth_provider == "clerk"
                    ]
                )
                unsynced_users = len(
                    [
                        u
                        for u in total_users
                        if not u.is_synced or u.auth_provider != "clerk"
                    ]
                )
                active_users = len([u for u in total_users if u.is_active])

                return {
                    "total_users": len(total_users),
                    "synced_users": synced_users,
                    "unsynced_users": unsynced_users,
                    "active_users": active_users,
                    "clerk_users": synced_users,
                }

        except Exception as e:
            raise UserSyncError(f"Failed to get sync stats: {str(e)}")
