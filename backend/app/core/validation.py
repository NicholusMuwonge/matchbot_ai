"""
Shared validation utilities for consistent input validation across the application.

This module provides reusable validation patterns and error handling.
"""

import re
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError


class ValidationUtils:
    """Shared validation utilities."""

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate email format using regex."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_team_type(team_type: str) -> bool:
        """Validate team type against allowed values."""
        allowed_types = {"corporate", "matchmaker_agency", "consulting", "enterprise"}
        return team_type in allowed_types

    @staticmethod
    def validate_organization_id(org_id: str) -> bool:
        """Validate organization ID format (Clerk format)."""
        pattern = r"^org_[a-zA-Z0-9]{28}$"
        return bool(re.match(pattern, org_id))

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format (Clerk format)."""
        pattern = r"^user_[a-zA-Z0-9]{28}$"
        return bool(re.match(pattern, user_id))

    @staticmethod
    def validate_required_fields(
        data: dict[str, Any], required_fields: list[str]
    ) -> None:
        """Validate that all required fields are present and non-empty."""
        missing_fields = []
        empty_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif not data[field] or (
                isinstance(data[field], str) and not data[field].strip()
            ):
                empty_fields.append(field)

        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        if empty_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Empty required fields: {', '.join(empty_fields)}",
            )

    @staticmethod
    def handle_validation_error(error: ValidationError) -> HTTPException:
        """Convert Pydantic ValidationError to HTTPException."""
        error_details = []
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            message = err["msg"]
            error_details.append(f"{field}: {message}")

        return HTTPException(
            status_code=422, detail=f"Validation failed: {'; '.join(error_details)}"
        )


class ErrorResponseBuilder:
    """Builder for consistent error responses."""

    @staticmethod
    def build_error_response(
        status_code: int, message: str, details: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build standardized error response."""
        response = {
            "error": True,
            "status_code": status_code,
            "message": message,
            "timestamp": f"{int(datetime.now().timestamp())}",
        }

        if details:
            response["details"] = details

        return response

    @staticmethod
    def authentication_error(message: str = "Authentication failed") -> HTTPException:
        """Create standardized authentication error."""
        return HTTPException(status_code=401, detail=message)

    @staticmethod
    def authorization_error(message: str = "Insufficient permissions") -> HTTPException:
        """Create standardized authorization error."""
        return HTTPException(status_code=403, detail=message)

    @staticmethod
    def not_found_error(resource: str = "Resource") -> HTTPException:
        """Create standardized not found error."""
        return HTTPException(status_code=404, detail=f"{resource} not found")

    @staticmethod
    def validation_error(message: str = "Invalid input") -> HTTPException:
        """Create standardized validation error."""
        return HTTPException(status_code=422, detail=message)
