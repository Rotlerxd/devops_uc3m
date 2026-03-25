"""Integration test fixtures — real PostgreSQL + FastAPI TestClient."""

import asyncio
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db, get_elastic
from app.main import app

# Test database URL — uses env var or falls back to docker-compose defaults
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://newsradar_admin:super_secret_password@localhost:5432/newsradar_db",
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=pool.NullPool)
TestAsyncSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[assignment]


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for all async tests in the session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def _setup_database():
    """Create all tables before tests, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session():
    """Provide a database session per test."""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    """Async HTTP test client with overridden DB dependency.

    Each test gets its own session created fresh inside the dependency override.
    """

    async def _override_get_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    async def _override_get_elastic():
        yield None  # mock ES in integration tests

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_elastic] = _override_get_elastic

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(client: AsyncClient):
    """Register a test user and return their data."""
    import unittest.mock

    with unittest.mock.patch("app.core.email.send_verification_email"):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration@test.com",
                "nombre": "Test",
                "apellidos": "User",
                "password": "testpass123",
            },
        )
    return response.json()
