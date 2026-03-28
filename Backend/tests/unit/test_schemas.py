"""Unit tests for Pydantic schemas — validation logic.

Since schemas are defined inline in app.main and importing main triggers a
DB connection at module level, we re-define minimal schema mirrors for
isolated unit testing. The real schemas are exercised by integration tests.
"""

import pytest
from pydantic import BaseModel, EmailStr, Field, ValidationError


class _UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization: str = Field(..., min_length=1, max_length=180)
    password: str = Field(..., min_length=6, max_length=128)


@pytest.mark.unit
class TestUserCreate:
    def test_valid_user(self):
        user = _UserCreate(
            email="test@uc3m.es",
            first_name="Ana",
            last_name="García",
            organization="UC3M",
            password="secure123",
        )
        assert user.email == "test@uc3m.es"
        assert user.first_name == "Ana"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            _UserCreate(
                email="not-an-email",
                first_name="Ana",
                last_name="García",
                organization="UC3M",
                password="secure123",
            )

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            _UserCreate(email="test@uc3m.es")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            _UserCreate(
                email="test@uc3m.es",
                first_name="Ana",
                last_name="García",
                organization="UC3M",
                password="12345",
            )
