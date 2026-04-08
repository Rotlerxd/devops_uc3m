"""Functional tests for auth endpoints — /login, /register, /verify."""

import pytest


@pytest.mark.functional
class TestRegister:
    def test_register_success(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "organization": "TestOrg",
                "password": "securepass",
                "role_ids": [1],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "Nuevo"
        assert "id" in data

    def test_register_duplicate_email(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "func@test.com",
                "first_name": "Duplicate",
                "last_name": "User",
                "organization": "TestOrg",
                "password": "securepass",
                "role_ids": [1],
            },
        )
        assert response.status_code == 409
        assert "ya está registrado" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "first_name": "Bad",
                "last_name": "Email",
                "organization": "TestOrg",
                "password": "securepass",
                "role_ids": [1],
            },
        )
        assert response.status_code == 422

    def test_register_missing_roles(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "noroles@test.com",
                "first_name": "No",
                "last_name": "Roles",
                "organization": "TestOrg",
                "password": "securepass",
                "role_ids": [999],
            },
        )
        assert response.status_code == 400


@pytest.mark.functional
class TestLogin:
    def test_login_success(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "func@test.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "func@test.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@test.com", "password": "whatever"},
        )
        assert response.status_code == 401


@pytest.mark.functional
class TestVerifyEmail:
    def test_verify_with_invalid_token(self, client):
        response = client.get("/api/v1/auth/verify?token=invalid.token.here")
        assert response.status_code == 400

    def test_verify_with_expired_token(self, client):

        from app.core.security import create_verification_token

        token = create_verification_token("expired@test.com")
        response = client.get(f"/api/v1/auth/verify?token={token}")
        assert response.status_code == 400
