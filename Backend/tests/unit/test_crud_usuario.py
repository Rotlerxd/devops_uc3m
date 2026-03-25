"""Unit tests for CRUD usuario operations — uses mocked DB session."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.crud.usuario import get_all_users, get_user_by_email
from app.models.usuario import RolUsuario, Usuario


def _make_mock_user(email="test@uc3m.es", nombre="Test", verified=False):
    user = MagicMock(spec=Usuario)
    user.email = email
    user.nombre = nombre
    user.password_hash = "$2b$12$fakehash"
    user.rol = RolUsuario.LECTOR
    user.is_verified = verified
    return user


@pytest.mark.unit
class TestGetUserByEmail:
    @pytest.mark.asyncio
    async def test_user_found(self):
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = _make_mock_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        user = await get_user_by_email(mock_session, "test@uc3m.es")
        assert user is not None
        assert user.email == "test@uc3m.es"

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        user = await get_user_by_email(mock_session, "nonexistent@uc3m.es")
        assert user is None


@pytest.mark.unit
class TestGetAllUsers:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [_make_mock_user(), _make_mock_user(email="other@uc3m.es")]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        users = await get_all_users(mock_session)
        assert len(users) == 2
