"""Integration test fixtures — real PostgreSQL + FastAPI TestClient (sync)."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# Test database URL — uses env var or falls back to docker-compose defaults
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://newsradar_user:newsradar_password@localhost:5432/newsradar_db",
)

test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Create all tables before tests, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session():
    """Provide a database session per test."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Sync HTTP test client with overridden DB dependency."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client: TestClient):
    """Register a test user and return their data."""
    import unittest.mock

    with unittest.mock.patch("app.core.security.send_verification_email"):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration@test.com",
                "first_name": "Test",
                "last_name": "User",
                "organization": "TestOrg",
                "password": "testpass123",
            },
        )
    return response.json()
