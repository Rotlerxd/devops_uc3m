"""Unit tests for app.db.models — User and Role model validation."""

import pytest

from app.db.models import Role, User


@pytest.mark.unit
class TestModels:
    def test_user_tablename(self):
        assert User.__tablename__ == "users"

    def test_role_tablename(self):
        assert Role.__tablename__ == "roles"

    def test_user_has_required_columns(self):
        columns = [c.name for c in User.__table__.columns]
        assert "id" in columns
        assert "email" in columns
        assert "hashed_password" in columns
        assert "first_name" in columns
        assert "last_name" in columns
        assert "is_verified" in columns

    def test_role_has_required_columns(self):
        columns = [c.name for c in Role.__table__.columns]
        assert "id" in columns
        assert "name" in columns
