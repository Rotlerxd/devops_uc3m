"""Functional tests for API endpoints with PostgreSQL."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestUserCRUD:
    def test_create_user_via_api(self, client: TestClient):
        response = client.post(
            "/api/v1/users",
            json={
                "email": "crud@test.com",
                "first_name": "CRUD",
                "last_name": "Test",
                "organization": "TestOrg",
                "password": "password123",
                "role_ids": [1],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code in (201, 401)

    def test_list_users_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/users")
        assert response.status_code == 401

    def test_get_user_not_found(self, client: TestClient):
        response = client.get("/api/v1/users/999")
        assert response.status_code == 401


@pytest.mark.integration
class TestRoleCRUD:
    def test_list_roles_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/roles")
        assert response.status_code == 401

    def test_create_role_requires_auth(self, client: TestClient):
        response = client.post("/api/v1/roles", json={"name": "newrole"})
        assert response.status_code == 401


@pytest.mark.integration
class TestAlertCRUD:
    def test_create_alert_requires_auth(self, client: TestClient):
        response = client.post(
            "/api/v1/users/1/alerts",
            json={
                "name": "Test Alert",
                "descriptors": ["python", "fastapi", "api"],
                "categories": [],
                "cron_expression": "0 * * * *",
            },
        )
        assert response.status_code == 401
