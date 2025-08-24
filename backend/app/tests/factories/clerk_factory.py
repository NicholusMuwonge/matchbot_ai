"""
Clerk API data factories - like Ruby Factory Bot
Generate realistic Clerk API responses and webhook payloads
"""

import random
from datetime import datetime

import factory
from factory import Faker, LazyAttribute, Sequence


class ClerkUserDataFactory(factory.DictFactory):
    """Factory for Clerk API user data (not our User model)"""

    # Clerk user ID format
    id = Sequence(lambda n: f"user_2{n:012d}")
    object = "user"

    # Basic info
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    username = None

    # Email addresses (Clerk format)
    email_addresses = LazyAttribute(
        lambda obj: [
            {
                "id": f"idn_{obj['id']}_email",
                "object": "email_address",
                "email_address": factory.Faker("email").generate({}),
                "verification": {"status": "verified", "strategy": "email_code"},
                "linked_to": [],
                "reserved": False,
            }
        ]
    )

    # Primary identifiers
    primary_email_address_id = LazyAttribute(
        lambda obj: obj["email_addresses"][0]["id"]
    )
    primary_phone_number_id = None
    primary_web3_wallet_id = None

    # Profile
    profile_image_url = "https://www.gravatar.com/avatar?d=mp"
    image_url = LazyAttribute(
        lambda obj: f"https://img.clerk.com/oauth_google/img_{obj['id']}"
    )

    # Security & metadata
    password_enabled = True
    two_factor_enabled = False
    phone_numbers = []
    web3_wallets = []
    external_accounts = []
    external_id = None

    # Metadata objects
    public_metadata = {}
    private_metadata = {}
    unsafe_metadata = {}

    # Additional fields
    birthday = ""
    gender = ""

    # Timestamps (Clerk uses milliseconds)
    created_at = LazyAttribute(lambda obj: int(datetime.utcnow().timestamp() * 1000))
    updated_at = LazyAttribute(lambda obj: obj["created_at"])
    last_sign_in_at = None  # New users haven't signed in


class ClerkWebhookFactory(factory.DictFactory):
    """Factory for Clerk webhook payloads"""

    object = "event"
    type = "user.created"
    data = factory.SubFactory(ClerkUserDataFactory)


class ClerkUserCreatedWebhookFactory(ClerkWebhookFactory):
    """Factory for user.created webhook"""

    type = "user.created"


class ClerkUserUpdatedWebhookFactory(ClerkWebhookFactory):
    """Factory for user.updated webhook"""

    type = "user.updated"
    data = factory.SubFactory(
        ClerkUserDataFactory,
        last_sign_in_at=LazyAttribute(
            lambda obj: int(datetime.utcnow().timestamp() * 1000) - 3600000
        ),
    )


class ClerkUserDeletedWebhookFactory(factory.DictFactory):
    """Factory for user.deleted webhook"""

    object = "event"
    type = "user.deleted"
    data = LazyAttribute(
        lambda obj: {
            "id": factory.Sequence(lambda n: f"user_2{n:012d}").generate({}),
            "object": "user",
            "deleted": True,
        }
    )


class ClerkOrganizationDataFactory(factory.DictFactory):
    """Factory for Clerk organization data"""

    id = Sequence(lambda n: f"org_{n:012d}")
    object = "organization"
    name = Faker("company")
    slug = LazyAttribute(
        lambda obj: obj["name"].lower().replace(" ", "-").replace(".", "")
    )

    # Organization metadata
    members_count = LazyAttribute(lambda obj: random.randint(1, 10))
    pending_invitations_count = 0
    public_metadata = {}
    private_metadata = {}

    # Timestamps
    created_at = LazyAttribute(lambda obj: int(datetime.utcnow().timestamp() * 1000))
    updated_at = LazyAttribute(lambda obj: obj["created_at"])

    # Creator
    created_by = Sequence(lambda n: f"user_2{n:012d}")

    # Image
    image_url = "https://img.clerk.com/org_default_image"


class ClerkOrganizationCreatedWebhookFactory(factory.DictFactory):
    """Factory for organization.created webhook"""

    object = "event"
    type = "organization.created"
    data = factory.SubFactory(ClerkOrganizationDataFactory)


class ClerkWebhookHeadersFactory(factory.DictFactory):
    """Factory for Clerk webhook headers"""

    svix_id = Sequence(lambda n: f"msg_test_{n:012d}")
    svix_timestamp = LazyAttribute(lambda obj: str(int(datetime.utcnow().timestamp())))
    svix_signature = "v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE="  # Mock signature
    content_type = "application/json"
    user_agent = "Svix-Webhooks/1.24"


class ClerkJWTPayloadFactory(factory.DictFactory):
    """Factory for Clerk JWT payload"""

    # Standard JWT claims
    sub = Sequence(lambda n: f"user_2{n:012d}")  # Clerk user ID
    iss = "https://clerk.example.com"
    aud = "https://api.example.com"

    # Timestamps
    iat = LazyAttribute(lambda obj: int((datetime.utcnow()).timestamp()))
    exp = LazyAttribute(lambda obj: obj["iat"] + 3600)  # 1 hour expiry

    # User claims
    email = Faker("email")
    email_verified = True
    first_name = Faker("first_name")
    last_name = Faker("last_name")

    # Custom claims (for RBAC later)
    org_id = None
    org_role = None


# Clerk factory traits
class ClerkTraits:
    """Clerk-specific test data variations"""

    @staticmethod
    def user_created(user_id: str = None, email: str = None):
        """User created webhook with specific data"""
        user_data = ClerkUserDataFactory()
        if user_id:
            user_data["id"] = user_id
        if email:
            user_data["email_addresses"][0]["email_address"] = email

        return ClerkUserCreatedWebhookFactory(data=user_data)

    @staticmethod
    def user_updated(user_id: str, email: str = None):
        """User updated webhook"""
        user_data = ClerkUserDataFactory(id=user_id)
        if email:
            user_data["email_addresses"][0]["email_address"] = email

        return ClerkUserUpdatedWebhookFactory(data=user_data)

    @staticmethod
    def user_deleted(user_id: str):
        """User deleted webhook"""
        return ClerkUserDeletedWebhookFactory(
            data={"id": user_id, "object": "user", "deleted": True}
        )

    @staticmethod
    def jwt_payload(user_id: str = None, email: str = None):
        """JWT payload with specific user"""
        payload = ClerkJWTPayloadFactory()
        if user_id:
            payload["sub"] = user_id
        if email:
            payload["email"] = email
        return payload

    @staticmethod
    def webhook_headers(webhook_id: str = None):
        """Webhook headers with specific ID"""
        headers = ClerkWebhookHeadersFactory()
        if webhook_id:
            headers["svix_id"] = webhook_id
        return headers

    @staticmethod
    def organization_created(org_name: str = None, creator_id: str = None):
        """Organization created webhook"""
        org_data = ClerkOrganizationDataFactory()
        if org_name:
            org_data["name"] = org_name
            org_data["slug"] = org_name.lower().replace(" ", "-")
        if creator_id:
            org_data["created_by"] = creator_id

        return ClerkOrganizationCreatedWebhookFactory(data=org_data)
