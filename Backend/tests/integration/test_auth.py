"""Integration tests for auth endpoints — /login, /register, /verify, /me."""

import unittest.mock

import pytest


@pytest.mark.integration
class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        with unittest.mock.patch("app.core.email.send_verification_email"):
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@test.com",
                    "nombre": "Nuevo",
                    "apellidos": "Usuario",
                    "password": "securepass",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["is_verified"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, registered_user):
        with unittest.mock.patch("app.core.email.send_verification_email"):
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "integration@test.com",
                    "nombre": "Duplicate",
                    "apellidos": "User",
                    "password": "securepass",
                },
            )
        assert response.status_code == 400
        assert "ya está registrado" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "nombre": "Bad",
                "apellidos": "Email",
                "password": "securepass",
            },
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client, registered_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "integration@test.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, registered_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "integration@test.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "ghost@test.com", "password": "whatever"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestMe:
    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, client, registered_user):
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "integration@test.com", "password": "testpass123"},
        )
        token = login_resp.json()["access_token"]
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "integration@test.com"

    @pytest.mark.asyncio
    async def test_me_without_token(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token(self, client):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
