"""Functional test fixtures — FastAPI TestClient with PostgreSQL."""

import unittest.mock

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """HTTP test client with mocked external calls."""
    with (
        unittest.mock.patch("app.main.check_elastic_connection"),
        unittest.mock.patch("app.main.create_seed_data"),
        unittest.mock.patch("app.main.rss_fetcher_engine"),
        unittest.mock.patch("app.core.security.send_verification_email"),
        TestClient(app) as c,
    ):
        yield c


@pytest.fixture
def registered_user(client: TestClient):
    """Register a test user and return their data."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "func@test.com",
            "first_name": "Func",
            "last_name": "Test",
            "organization": "TestOrg",
            "password": "testpass123",
            "role_ids": [1],
        },
    )
    assert response.status_code == 200
    return response.json()
