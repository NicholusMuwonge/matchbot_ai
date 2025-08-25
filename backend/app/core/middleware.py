"""
Security middleware and decorators for Clerk authentication
"""

import functools
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.services.clerk_auth import ClerkAuthenticationError, ClerkService


def clerk_auth_required(func: Callable) -> Callable:
    """
    Decorator to require Clerk authentication for route handlers

    Usage:
        @router.get("/protected")
        @clerk_auth_required
        async def protected_route():
            return {"message": "You are authenticated!"}
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = None

        # Find the Request object in arguments
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if not request:
            raise HTTPException(
                status_code=500,
                detail="Request object not found - decorator misconfigured",
            )

        # Extract Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
            )

        session_token = authorization.replace("Bearer ", "")

        try:
            # Validate session token with Clerk
            clerk_service = ClerkService()
            session_data = clerk_service.validate_session_token(session_token)

            if not session_data.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session token",
                )

            # Add session data to request state
            request.state.clerk_session = session_data
            request.state.clerk_user_id = session_data.get("user_id")

            return await func(*args, **kwargs)

        except ClerkAuthenticationError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}",
            )

    return wrapper


def clerk_superuser_required(func: Callable) -> Callable:
    """
    Decorator to require Clerk authentication + superuser privileges

    Usage:
        @router.delete("/admin/users/{user_id}")
        @clerk_superuser_required
        async def delete_user(user_id: str):
            return {"message": "User deleted"}
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = None
        session = None

        # Find the Request and Session objects in arguments
        for arg in args:
            if isinstance(arg, Request):
                request = arg

        # Import here to avoid circular imports
        from sqlmodel import Session, select

        from app.models import User

        for arg in args:
            if isinstance(arg, Session):
                session = arg
                break

        if not request or not session:
            raise HTTPException(
                status_code=500,
                detail="Request or Session object not found - decorator misconfigured",
            )

        # First run clerk_auth_required logic
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
            )

        session_token = authorization.replace("Bearer ", "")

        try:
            clerk_service = ClerkService()
            session_data = clerk_service.validate_session_token(session_token)

            if not session_data.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session token",
                )

            clerk_user_id = session_data.get("user_id")
            if not clerk_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session - no user ID",
                )

            # Check if user is superuser
            statement = select(User).where(User.clerk_user_id == clerk_user_id)
            user = session.exec(statement).first()

            if not user:
                raise HTTPException(
                    status_code=404, detail="User not found in database"
                )

            if not user.is_superuser:
                raise HTTPException(
                    status_code=403, detail="Superuser privileges required"
                )

            # Add session and user data to request state
            request.state.clerk_session = session_data
            request.state.clerk_user_id = clerk_user_id
            request.state.current_user = user

            return await func(*args, **kwargs)

        except ClerkAuthenticationError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}",
            )

    return wrapper


class ClerkAuthMiddleware:
    """
    Middleware to add Clerk authentication context to all requests
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Add Clerk authentication context if Authorization header is present
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                session_token = authorization.replace("Bearer ", "")

                try:
                    clerk_service = ClerkService()
                    session_data = clerk_service.validate_session_token(session_token)

                    if session_data.get("valid"):
                        # Add Clerk context to request scope
                        scope["clerk_session"] = session_data
                        scope["clerk_user_id"] = session_data.get("user_id")
                        scope["clerk_authenticated"] = True
                    else:
                        scope["clerk_authenticated"] = False

                except Exception:
                    # Don't fail the request - just mark as not authenticated
                    scope["clerk_authenticated"] = False
            else:
                scope["clerk_authenticated"] = False

        await self.app(scope, receive, send)
