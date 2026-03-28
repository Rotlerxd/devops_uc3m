"""Integration tests for auth endpoints — /login, /register, /verify, /me."""

import unittest.mock

import pytest


@pytest.mark.integration
class TestRegister:
    def test_register_success(self, client):
        with unittest.mock.patch("app.core.security.send_verification_email"):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@test.com",
                    "first_name": "Nuevo",
                    "last_name": "Usuario",
                    "organization": "TestOrg",
                    "password": "securepass",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "Nuevo"
        assert "id" in data

    def test_register_duplicate_email(self, client, registered_user):
        with unittest.mock.patch("app.core.security.send_verification_email"):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "integration@test.com",
                    "first_name": "Duplicate",
                    "last_name": "User",
                    "organization": "TestOrg",
                    "password": "securepass",
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
            },
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestLogin:
    def test_login_success(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "integration@test.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "integration@test.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@test.com", "password": "whatever"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestMe:
    def test_me_with_valid_token(self, client, registered_user):
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "integration@test.com", "password": "testpass123"},
        )
        token = login_resp.json()["access_token"]
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "integration@test.com"

    def test_me_without_token(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self, client):
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
