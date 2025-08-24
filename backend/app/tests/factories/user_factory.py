"""
User model factories
Clean test data generation for User models
"""

import factory
from factory import Faker, Sequence

from app.models import User


class UserFactory(factory.Factory):
    """Factory for creating User models in tests"""

    class Meta:
        model = User

    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    clerk_user_id = Sequence(lambda n: f"user_test_{n:06d}")
    auth_provider = "clerk"
    is_synced = True
    email_verified = True
    profile_image_url = Faker("image_url")
    created_at = Faker("date_time_this_year", tzinfo=None)
    last_login = Faker("date_time_this_month", tzinfo=None)
    account_id = None


class ClerkUserFactory(UserFactory):
    """Factory for users created via Clerk webhook"""

    clerk_user_id = Sequence(lambda n: f"user_2{n:012d}")
    profile_image_url = "https://www.gravatar.com/avatar?d=mp"
    is_synced = True


class UnverifiedUserFactory(UserFactory):
    """Factory for unverified users"""

    email_verified = False
    last_login = None
    is_synced = False


class AdminUserFactory(UserFactory):
    """Factory for admin users"""

    email = "admin@example.com"
    first_name = "Admin"
    last_name = "User"


class UserTraits:
    """Common user variations for tests"""

    @staticmethod
    def with_clerk_id(clerk_id: str):
        return UserFactory(clerk_user_id=clerk_id)

    @staticmethod
    def with_email(email: str):
        return UserFactory(email=email)

    @staticmethod
    def verified():
        return UserFactory(email_verified=True, is_synced=True)

    @staticmethod
    def unverified():
        return UnverifiedUserFactory()

    @staticmethod
    def admin():
        return AdminUserFactory()


class UserFactoryDB(UserFactory):
    """Factory that saves to database"""

    class Meta:
        model = User
