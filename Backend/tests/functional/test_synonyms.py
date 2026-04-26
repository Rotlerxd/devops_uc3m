"""Functional tests for alert synonym endpoint."""

import httpx
import pytest
from fastapi import HTTPException

from app.main import app, get_current_user


@pytest.mark.integration
class TestSynonymEndpoint:
    async def test_generate_alert_synonyms(self, monkeypatch):
        async def current_user_override():
            return object()

        app.dependency_overrides[get_current_user] = current_user_override
        monkeypatch.setattr("app.main.generate_synonyms", lambda term, limit, language: ["auto", "carro", "vehiculo"])

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/alerts/synonyms?term=coche&limit=3")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["term"] == "coche"
        assert data["language"] == "spa"
        assert data["limit"] == 3
        assert data["synonyms"] == ["auto", "carro", "vehiculo"]

    async def test_generate_alert_synonyms_requires_auth(self):
        async def unauthorized_override():
            raise HTTPException(status_code=401, detail="Token inválido o ausente")

        app.dependency_overrides[get_current_user] = unauthorized_override

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/alerts/synonyms?term=coche&limit=3")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 401
