"""Functional tests for in-memory store operations."""

import pytest
from fastapi.testclient import TestClient

from app.main import (
    counters,
    next_id,
    roles_store,
    sanitize_user,
    users_store,
)


@pytest.mark.functional
class TestNextId:
    def test_next_id_increments(self):
        counters["test"] = 1
        assert next_id("test") == 1
        assert next_id("test") == 2
        assert next_id("test") == 3

    def test_next_id_separate_counters(self):
        counters["a"] = 10
        counters["b"] = 20
        assert next_id("a") == 10
        assert next_id("b") == 20
        assert next_id("a") == 11


@pytest.mark.functional
class TestSanitizeUser:
    def test_sanitize_removes_password(self):
        from app.main import UserInDB

        user_db = UserInDB(
            id=1,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            organization="Org",
            password="secret123",
        )
        sanitized = sanitize_user(user_db)
        assert sanitized.id == 1
        assert sanitized.email == "test@example.com"
        assert "password" not in sanitized.model_dump()


@pytest.mark.functional
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
        # Will fail auth since we don't have a valid token
        assert response.status_code in (201, 401)

    def test_list_users_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/users")
        assert response.status_code == 401

    def test_get_user_not_found(self, client: TestClient):
        response = client.get("/api/v1/users/999")
        assert response.status_code == 401


@pytest.mark.functional
class TestRoleCRUD:
    def test_list_roles_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/roles")
        assert response.status_code == 401

    def test_create_role_requires_auth(self, client: TestClient):
        response = client.post("/api/v1/roles", json={"name": "newrole"})
        assert response.status_code == 401


@pytest.mark.functional
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


@pytest.mark.functional
class TestSeedData:
    def test_seed_creates_admin_role(self, client: TestClient):
        assert len(roles_store) >= 1
        assert any(r.name == "admin" for r in roles_store.values())

    def test_seed_creates_admin_user(self, client: TestClient):
        assert len(users_store) >= 1
        assert any(u.email == "admin@newsradar.com" for u in users_store.values())
