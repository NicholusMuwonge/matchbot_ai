"""
Seeder runner for executing all or specific seeders.
"""

from typing import Any

from sqlmodel import Session

from app.seeders import RBACSeeder


class SeederRunner:
    """Runner for executing database seeders."""

    # Registry of available seeders
    SEEDERS = {
        "rbac": RBACSeeder,
    }

    @classmethod
    def run_all(cls, session: Session, force_update: bool = False) -> dict[str, Any]:
        """
        Run all available seeders.

        Args:
            session: Database session
            force_update: Whether to update existing records

        Returns:
            Dictionary with results for each seeder
        """
        results = {}

        for name, seeder_class in cls.SEEDERS.items():
            try:
                results[name] = seeder_class.seed(session, force_update)
            except Exception as e:
                results[name] = {
                    "created": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": [f"Seeder failed: {str(e)}"],
                }

        return results

    @classmethod
    def run_seeder(
        cls, seeder_name: str, session: Session, force_update: bool = False
    ) -> dict[str, Any]:
        """
        Run a specific seeder.

        Args:
            seeder_name: Name of the seeder to run
            session: Database session
            force_update: Whether to update existing records

        Returns:
            Dictionary with seeding results

        Raises:
            ValueError: If seeder name is not found
        """
        if seeder_name not in cls.SEEDERS:
            available = list(cls.SEEDERS.keys())
            raise ValueError(
                f"Seeder '{seeder_name}' not found. Available: {available}"
            )

        seeder_class = cls.SEEDERS[seeder_name]
        return seeder_class.seed(session, force_update)

    @classmethod
    def get_summary(cls, session: Session) -> dict[str, Any]:
        """
        Get summary from all seeders.

        Args:
            session: Database session

        Returns:
            Dictionary with summary from each seeder
        """
        summaries = {}

        for name, seeder_class in cls.SEEDERS.items():
            try:
                summaries[name] = seeder_class.get_summary(session)
            except Exception as e:
                summaries[name] = {"error": f"Failed to get summary: {str(e)}"}

        return summaries

    @classmethod
    def list_seeders(cls) -> list[str]:
        """Get list of available seeder names."""
        return list(cls.SEEDERS.keys())
