"""
Test configuration and fixtures.
Similar to Ruby's spec_helper.rb or rails_helper.rb

This file is automatically loaded by pytest and provides:
- Database setup/teardown
- Common fixtures (like FactoryBot factories)
- Test utilities
"""

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.models.rbac import Role
from app.models.user import User


@pytest.fixture(name="session")
def session_fixture():
    """
    Create a test database session.

    Similar to Ruby's:
    - DatabaseCleaner.strategy = :transaction
    - let(:session) { ... }

    This creates an in-memory SQLite database for each test,
    ensuring test isolation.
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        # Automatic cleanup after test


@pytest.fixture
def sample_role(session: Session) -> Role:
    """
    Create a sample role for testing.

    Similar to Ruby's:
    - let(:role) { create(:role) }
    - FactoryBot.create(:role)
    """
    role = Role(
        name="test_role",
        display_name="Test Role",
        description="A test role",
        permissions=["users:read", "users:write"],
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@pytest.fixture
def sample_user(session: Session) -> User:
    """
    Create a sample user for testing.

    Similar to Ruby's:
    - let(:user) { create(:user) }
    """
    user = User(
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        hashed_password="hashed",  # In real tests, use proper hashing
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def app_owner_role(session: Session) -> Role:
    """Create an app owner role with all permissions."""
    role = Role(
        name="app_owner",
        display_name="Application Owner",
        description="Full access",
        permissions=["*"],
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    return role
