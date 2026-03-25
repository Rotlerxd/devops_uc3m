"""Integration tests for /health and / endpoints."""

import pytest


@pytest.mark.integration
class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_root_returns_message(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "NEWSRADAR" in data["message"]
