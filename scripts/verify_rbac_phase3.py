#!/usr/bin/env python3
"""
Phase 3 RBAC Verification Script

This script helps verify that Clerk configuration is working correctly
by testing session claims and role-based API access.

Usage:
    python scripts/verify_rbac_phase3.py --email your-email@domain.com

Requirements:
    - Backend server running
    - User exists in database with assigned role
    - Clerk session token configured with role claims
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def setup_backend_imports():
    """Setup backend imports with proper path handling"""
    backend_dir = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))

    try:
        # Import backend modules after path setup
        from app.database import SessionLocal
        from app.models.user import User
        from app.models.role import UserRole
        from app.services.role_service import RoleService
        from sqlalchemy.orm import joinedload

        return SessionLocal, User, UserRole, RoleService, joinedload
    except ImportError as e:
        print(f"❌ Failed to import backend modules: {e}")
        print(
            "Make sure you're running from the project root and backend is set up correctly."
        )
        sys.exit(1)


class RBACPhase3Verifier:
    """Verify Phase 3 RBAC configuration"""

    def __init__(self):
        # Import backend modules
        SessionLocal, User, UserRole, RoleService, joinedload = setup_backend_imports()

        # Store imports for class use
        self.SessionLocal = SessionLocal
        self.User = User
        self.UserRole = UserRole
        self.RoleService = RoleService
        self.joinedload = joinedload

        # Initialize database and services
        self.db = SessionLocal()
        self.role_service = RoleService(self.db)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    async def verify_user_role_assignment(self, email: str) -> dict:
        """Verify user exists and has role assigned in database"""
        print(f"\n🔍 Checking database role assignment for {email}...")

        try:
            # Find user by email
            user = self.db.query(self.User).filter(self.User.email == email).first()
            if not user:
                return {
                    "status": "error",
                    "message": f"User {email} not found in database",
                    "suggestions": [
                        "Ensure user has signed up and webhook processed",
                        "Check webhook logs for errors",
                        "Manually create user if needed",
                    ],
                }

            # Get user's roles
            user_roles = (
                self.db.query(self.UserRole)
                .options(self.joinedload(self.UserRole.role))
                .filter(self.UserRole.user_id == user.id)
                .all()
            )

            if not user_roles:
                return {
                    "status": "error",
                    "message": f"No roles assigned to user {email}",
                    "user_id": str(user.id),
                    "clerk_id": user.clerk_id,
                    "suggestions": [
                        "Check webhook role assignment logic",
                        "Manually assign role using admin API",
                        "Verify role seeding completed successfully",
                    ],
                }

            # Format role information
            roles_info = []
            for user_role in user_roles:
                roles_info.append(
                    {
                        "role_name": user_role.role.name,
                        "permissions": user_role.role.permissions,
                        "assigned_at": user_role.assigned_at.isoformat(),
                    }
                )

            return {
                "status": "success",
                "message": f"User {email} found with {len(roles_info)} role(s)",
                "user_id": str(user.id),
                "clerk_id": user.clerk_id,
                "roles": roles_info,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Database query failed: {str(e)}",
                "suggestions": [
                    "Check database connection",
                    "Verify tables exist (run migrations)",
                    "Check backend configuration",
                ],
            }

    def verify_role_definitions(self) -> dict:
        """Verify all expected roles exist with correct permissions"""
        print("\n🔍 Checking role definitions...")

        try:
            expected_roles = {
                "app_owner": ["*"],
                "platform_admin": ["users:*", "analytics:*"],
                "support_admin": ["users:read", "tickets:*"],
                "regular_user": ["profile:read", "profile:write"],
            }

            results = {}
            all_roles = self.role_service.get_all_roles()

            for role in all_roles:
                results[role.name] = {
                    "exists": True,
                    "permissions": role.permissions,
                    "expected": role.name in expected_roles,
                    "permissions_match": role.name in expected_roles
                    and set(role.permissions) == set(expected_roles.get(role.name, [])),
                }

            # Check for missing expected roles
            existing_names = {role.name for role in all_roles}
            missing_roles = set(expected_roles.keys()) - existing_names

            return {
                "status": "success" if not missing_roles else "warning",
                "message": f"Found {len(all_roles)} roles in database",
                "roles": results,
                "missing_roles": list(missing_roles),
                "suggestions": [
                    "Run role seeder if roles are missing",
                    "Check migration files if tables don't exist",
                ]
                if missing_roles
                else [],
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to verify roles: {str(e)}",
                "suggestions": [
                    "Check database connection",
                    "Verify role tables exist",
                    "Run migrations and seeders",
                ],
            }

    def generate_clerk_metadata_instructions(self, email: str, role_info: dict) -> dict:
        """Generate instructions for setting Clerk metadata"""
        if role_info["status"] != "success":
            return {"status": "skipped", "message": "User role verification failed"}

        primary_role = role_info["roles"][0]["role_name"]
        is_app_owner = primary_role == "app_owner"

        metadata = {"role": primary_role, "isAppOwner": is_app_owner}

        return {
            "status": "info",
            "message": "Clerk Dashboard metadata configuration",
            "clerk_metadata": metadata,
            "instructions": [
                "1. Go to Clerk Dashboard → Users",
                f"2. Find user with email: {email}",
                "3. Click on the user",
                "4. Go to 'Metadata' tab",
                "5. Edit 'Public Metadata'",
                f"6. Set metadata to: {json.dumps(metadata, indent=2)}",
                "7. Save changes",
                "8. User should log out and log back in to refresh token",
            ],
        }

    def generate_session_token_config(self) -> dict:
        """Generate session token configuration for Clerk"""
        config = {
            "role": "{{user.public_metadata.role}}",
            "isAppOwner": "{{user.public_metadata.isAppOwner}}",
        }

        return {
            "status": "info",
            "message": "Clerk session token configuration",
            "session_config": config,
            "instructions": [
                "1. Go to Clerk Dashboard → Sessions",
                "2. Click 'Edit session token'",
                f"3. Replace configuration with: {json.dumps(config, indent=2)}",
                "4. Save changes",
                "5. All users will need to refresh their sessions",
            ],
        }

    def print_results(self, results: dict):
        """Pretty print verification results"""
        status_icons = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️",
            "skipped": "⏭️",
        }

        for key, result in results.items():
            if isinstance(result, dict) and "status" in result:
                icon = status_icons.get(result["status"], "❓")
                print(f"\n{icon} {key.replace('_', ' ').title()}")
                print(f"   {result['message']}")

                if "suggestions" in result and result["suggestions"]:
                    print("   Suggestions:")
                    for suggestion in result["suggestions"]:
                        print(f"   • {suggestion}")

                if "instructions" in result and result["instructions"]:
                    print("   Instructions:")
                    for instruction in result["instructions"]:
                        print(f"   {instruction}")

                if "roles" in result and result["roles"]:
                    print("   Roles found:")
                    for role_name, role_data in result["roles"].items():
                        status = "✅" if role_data.get("permissions_match") else "⚠️"
                        print(f"   {status} {role_name}: {role_data['permissions']}")

                if "clerk_metadata" in result:
                    print(
                        f"   Metadata: {json.dumps(result['clerk_metadata'], indent=6)}"
                    )

                if "session_config" in result:
                    print(
                        f"   Config: {json.dumps(result['session_config'], indent=6)}"
                    )


async def main():
    """Main verification workflow"""
    parser = argparse.ArgumentParser(description="Verify Phase 3 RBAC configuration")
    parser.add_argument("--email", required=True, help="Email of user to verify")
    args = parser.parse_args()

    print("🚀 Phase 3 RBAC Verification Starting...")
    print("=" * 50)

    with RBACPhase3Verifier() as verifier:
        results = {}

        # 1. Verify role definitions
        results["role_definitions"] = verifier.verify_role_definitions()

        # 2. Verify user role assignment
        results["user_role_assignment"] = await verifier.verify_user_role_assignment(
            args.email
        )

        # 3. Generate Clerk configuration instructions
        results["clerk_metadata"] = verifier.generate_clerk_metadata_instructions(
            args.email, results["user_role_assignment"]
        )
        results["session_token"] = verifier.generate_session_token_config()

        # Print all results
        verifier.print_results(results)

        # Summary
        print("\n" + "=" * 50)
        success_count = sum(
            1
            for r in results.values()
            if isinstance(r, dict) and r.get("status") == "success"
        )
        total_checks = len(
            [
                r
                for r in results.values()
                if isinstance(r, dict)
                and r.get("status") in ["success", "error", "warning"]
            ]
        )

        if success_count == total_checks:
            print("🎉 All verifications passed! Ready for Phase 4.")
        else:
            print(
                f"⚠️  {total_checks - success_count} issue(s) found. Fix before proceeding."
            )

        print("\n📋 Next Steps:")
        print("1. Apply Clerk Dashboard configurations shown above")
        print("2. Test frontend session claims")
        print("3. Proceed to Phase 4: Frontend Integration")


if __name__ == "__main__":
    asyncio.run(main())
