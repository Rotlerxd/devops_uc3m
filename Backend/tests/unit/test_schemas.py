"""Unit tests for Pydantic schemas — validation logic."""

import pytest
from pydantic import ValidationError

from app.schemas.usuario import UsuarioCreate, UsuarioResponse


@pytest.mark.unit
class TestUsuarioCreate:
    def test_valid_user(self):
        user = UsuarioCreate(
            email="test@uc3m.es",
            nombre="Ana",
            apellidos="García",
            password="secure123",
        )
        assert user.email == "test@uc3m.es"
        assert user.nombre == "Ana"
        assert user.organizacion is None

    def test_valid_user_with_org(self):
        user = UsuarioCreate(
            email="test@uc3m.es",
            nombre="Ana",
            apellidos="García",
            organizacion="UC3M",
            password="secure123",
        )
        assert user.organizacion == "UC3M"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UsuarioCreate(
                email="not-an-email",
                nombre="Ana",
                apellidos="García",
                password="secure123",
            )

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            UsuarioCreate(email="test@uc3m.es")  # missing nombre, apellidos, password


@pytest.mark.unit
class TestUsuarioResponse:
    def test_response_schema(self):
        data = {
            "id": 1,
            "email": "user@uc3m.es",
            "nombre": "Carlos",
            "apellidos": "López",
            "organizacion": None,
            "rol": "lector",
            "is_verified": False,
        }
        resp = UsuarioResponse(**data)
        assert resp.id == 1
        assert resp.rol.value == "lector"
