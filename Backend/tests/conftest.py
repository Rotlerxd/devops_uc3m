"""Shared pytest fixtures for all backend tests."""

import os

import pytest

# Force test environment variables before any app imports
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://newsradar_admin:super_secret_password@localhost:5432/newsradar_db"
)
os.environ.setdefault("ELASTIC_URL", "http://localhost:9200")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("MAIL_SERVER", "localhost")
os.environ.setdefault("MAIL_PORT", "2525")
os.environ.setdefault("MAIL_USERNAME", "test")
os.environ.setdefault("MAIL_PASSWORD", "test")
os.environ.setdefault("MAIL_FROM", "test@newsradar.local")


@pytest.fixture(autouse=True)
def _env_setup():
    """Ensure test environment variables are set for every test."""
    yield
