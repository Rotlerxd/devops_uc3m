"""Shared pytest fixtures for all backend tests."""

import os

import pytest

# Force test environment variables before any app imports
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("MAILTRAP_HOST", "localhost")
os.environ.setdefault("MAILTRAP_PORT", "2525")
os.environ.setdefault("MAIL_USERNAME", "test")
os.environ.setdefault("MAIL_PASSWORD", "test")


@pytest.fixture(autouse=True)
def _env_setup():
    """Ensure test environment variables are set for every test."""
    yield
