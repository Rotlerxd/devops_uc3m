"""Integration tests for API endpoints in main.py."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestUserEndpoints:
    def test_list_users_as_admin(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_user_as_admin(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.post(
            "/api/v1/users",
            json={
                "email": "newuser@test.com",
                "first_name": "New",
                "last_name": "User",
                "organization": "TestOrg",
                "password": "password123",
                "role_ids": [1],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"

    def test_get_user_by_id(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/users/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data

    def test_update_user(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.put(
            "/api/v1/users/1",
            json={"first_name": "UpdatedName"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_delete_user(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.delete(
            "/api/v1/users/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 204, 400)

    def test_user_not_found(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/users/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestRoleEndpoints:
    def test_list_roles_as_admin(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_create_role_as_admin(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        role_name = f"test_role_{counters['roles']}"
        response = client.post(
            "/api/v1/roles",
            json={"name": role_name},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_get_role_by_id(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/roles/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_update_role(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.put(
            "/api/v1/roles/1",
            json={"name": "updated_role_name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_delete_role(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.delete(
            "/api/v1/roles/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 204, 400, 409)


@pytest.mark.integration
class TestCategoryEndpoints:
    def test_list_categories(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_category(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.post(
            "/api/v1/categories",
            json={"name": "Test Category", "source": "IPTC"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_get_category(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/categories/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_update_category(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.put(
            "/api/v1/categories/1",
            json={"name": "Updated Category"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_delete_category(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.delete(
            "/api/v1/categories/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 204, 400, 409)


@pytest.mark.integration
class TestStatsEndpoints:
    def test_list_stats(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_stats(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/stats/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestInformationSourceEndpoints:
    def test_list_sources(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/information-sources",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_source(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.post(
            "/api/v1/information-sources",
            json={"name": "Test Source", "url": "https://test.com/rss"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_get_source(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/information-sources/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestRSSChannelEndpoints:
    def test_list_channels_for_source(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.get(
            "/api/v1/information-sources/1/rss-channels",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_channel_for_source(self, client: TestClient):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@newsradar.com", "password": "admin123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Admin user not available or password changed")
        token = login_response.json()["access_token"]
        response = client.post(
            "/api/v1/information-sources/1/rss-channels",
            json={
                "url": "https://test.com/feed.xml",
                "category_id": 1,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
