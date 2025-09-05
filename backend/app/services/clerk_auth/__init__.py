"""
Clerk Authentication Services

Clerk API integration for user authentication and management.
"""

from .clerk_service import ClerkAuthenticationError, ClerkService

# Main exports for easy importing
__all__ = [
    "ClerkService",
    "ClerkAuthenticationError",
]
