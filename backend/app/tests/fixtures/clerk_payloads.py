"""
Realistic Clerk webhook payloads for testing
Based on actual Clerk API responses
"""

from datetime import datetime, timezone


def get_user_created_payload(
    user_id: str = "user_2abc123def456", email: str = "test@example.com"
):
    """Real Clerk user.created webhook payload structure"""
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    return {
        "data": {
            "birthday": "",
            "created_at": timestamp,
            "email_addresses": [
                {
                    "email_address": email,
                    "id": f"idn_{user_id}_email",
                    "linked_to": [],
                    "object": "email_address",
                    "reserved": False,
                    "verification": {"status": "verified", "strategy": "email_code"},
                }
            ],
            "external_accounts": [],
            "external_id": None,
            "first_name": "John",
            "gender": "",
            "id": user_id,
            "image_url": "https://img.clerk.com/eyJ0eXBlIjoicHJveHkiLCJzcmMiOiJodHRwczovL2ltYWdlcy5jbGVyay5kZXYvb2F1dGhfZ29vZ2xlL2ltZ18ye3VzZXJfaWR9In0",
            "last_name": "Doe",
            "last_sign_in_at": None,  # New user, no sign in yet
            "object": "user",
            "password_enabled": True,
            "phone_numbers": [],
            "primary_email_address_id": f"idn_{user_id}_email",
            "primary_phone_number_id": None,
            "primary_web3_wallet_id": None,
            "private_metadata": {},
            "profile_image_url": "https://www.gravatar.com/avatar?d=mp",
            "public_metadata": {},
            "two_factor_enabled": False,
            "unsafe_metadata": {},
            "updated_at": timestamp,
            "username": None,
            "web3_wallets": [],
        },
        "object": "event",
        "type": "user.created",
    }


def get_user_updated_payload(
    user_id: str = "user_existing123", email: str = "updated@example.com"
):
    """Real Clerk user.updated webhook payload structure"""
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    return {
        "data": {
            "birthday": "",
            "created_at": timestamp - 86400000,  # Created yesterday
            "email_addresses": [
                {
                    "email_address": email,
                    "id": f"idn_{user_id}_email",
                    "linked_to": [],
                    "object": "email_address",
                    "reserved": False,
                    "verification": {"status": "verified", "strategy": "email_code"},
                }
            ],
            "external_accounts": [],
            "external_id": None,
            "first_name": "Updated",
            "gender": "",
            "id": user_id,
            "image_url": "https://img.clerk.com/updated_user_image",
            "last_name": "Name",
            "last_sign_in_at": timestamp - 3600000,  # Signed in 1 hour ago
            "object": "user",
            "password_enabled": True,
            "phone_numbers": [],
            "primary_email_address_id": f"idn_{user_id}_email",
            "primary_phone_number_id": None,
            "primary_web3_wallet_id": None,
            "private_metadata": {},
            "profile_image_url": "https://www.gravatar.com/avatar?d=mp",
            "public_metadata": {},
            "two_factor_enabled": False,
            "unsafe_metadata": {},
            "updated_at": timestamp,
            "username": None,
            "web3_wallets": [],
        },
        "object": "event",
        "type": "user.updated",
    }


def get_user_deleted_payload(user_id: str = "user_deleted123"):
    """Real Clerk user.deleted webhook payload structure"""
    return {
        "data": {"deleted": True, "id": user_id, "object": "user"},
        "object": "event",
        "type": "user.deleted",
    }


def get_organization_created_payload(
    org_id: str = "org_abc123", creator_id: str = "user_creator123"
):
    """Real Clerk organization.created webhook payload structure"""
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    return {
        "data": {
            "created_at": timestamp,
            "created_by": creator_id,
            "id": org_id,
            "image_url": "https://img.clerk.com/org_default_image",
            "members_count": 1,
            "name": "Acme Corporation",
            "object": "organization",
            "pending_invitations_count": 0,
            "private_metadata": {},
            "public_metadata": {},
            "slug": "acme-corp",
            "updated_at": timestamp,
        },
        "object": "event",
        "type": "organization.created",
    }


def get_valid_webhook_headers(webhook_id: str = "msg_unique123"):
    """Real Clerk webhook headers structure"""
    return {
        "svix-id": webhook_id,
        "svix-timestamp": str(int(datetime.now(timezone.utc).timestamp())),
        "svix-signature": "v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=",
        "content-type": "application/json",
        "user-agent": "Svix-Webhooks/1.24",
    }
