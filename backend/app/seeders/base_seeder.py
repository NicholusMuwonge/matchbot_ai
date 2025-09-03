"""
Base seeder class for consistent seeding patterns.
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlmodel import Session


class BaseSeeder(ABC):
    """Abstract base class for database seeders."""

    @abstractmethod
    def seed(self, session: Session, force_update: bool = False) -> dict[str, Any]:
        """
        Seed data into the database.

        Args:
            session: Database session
            force_update: Whether to update existing records

        Returns:
            Dictionary with seeding results (created, updated, skipped, errors)
        """
        pass

    @abstractmethod
    def get_data(self) -> list:
        """
        Get the data to be seeded.

        Returns:
            List of data items to be seeded
        """
        pass

    def get_summary(self, session: Session) -> dict[str, Any]:
        """
        Get a summary of seeded data.

        Args:
            session: Database session

        Returns:
            Summary dictionary
        """
        return {"message": "Summary not implemented for this seeder"}
