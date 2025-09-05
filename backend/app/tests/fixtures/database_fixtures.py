from collections.abc import Generator

import pytest
from sqlmodel import Session, delete

from app.core.db import engine, init_db
from app.models import Item, User


@pytest.fixture(scope="session")
def db_engine():
    return engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(db_engine):
    with Session(db_engine) as session:
        init_db(session)
        session.commit()
    yield
    with Session(db_engine) as session:
        try:
            statement = delete(Item)
            session.execute(statement)
            statement = delete(User)
            session.execute(statement)
            session.commit()
        except Exception:
            session.rollback()


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    with Session(db_engine) as session:
        transaction = session.begin()

        try:
            yield session
        except Exception:
            transaction.rollback()
            raise
        finally:
            if transaction.is_active:
                transaction.rollback()
