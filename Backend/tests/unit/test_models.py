"""Unit tests for in-memory Pydantic models from main.py."""

import pytest
from pydantic import ValidationError

from app.main import (
    Alert,
    AlertCreate,
    CategoryCreate,
    InformationSourceCreate,
    Notification,
    Role,
    RSSChannel,
    User,
    UserCreate,
    UserInDB,
    UserUpdate,
)


@pytest.mark.unit
class TestRoleModel:
    def test_create_role(self):
        role = Role(id=1, name="admin")
        assert role.id == 1
        assert role.name == "admin"

    def test_role_name_min_length(self):
        with pytest.raises(ValidationError):
            Role(id=1, name="")

    def test_role_name_max_length(self):
        with pytest.raises(ValidationError):
            Role(id=1, name="a" * 101)


@pytest.mark.unit
class TestUserModels:
    def test_user_create_valid(self):
        user = UserCreate(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            organization="TestOrg",
            password="secure123",
        )
        assert user.email == "test@example.com"
        assert user.is_verified is False

    def test_user_in_db(self):
        user = UserInDB(
            id=1,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            organization="TestOrg",
            password="hashed_password",
        )
        assert user.id == 1
        assert user.password == "hashed_password"

    def test_user_response(self):
        user = User(
            id=1,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            organization="TestOrg",
        )
        assert user.id == 1
        assert "password" not in user.model_dump()

    def test_user_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                first_name="Test",
                last_name="User",
                organization="TestOrg",
                password="secure123",
            )

    def test_user_first_name_min_length(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                first_name="",
                last_name="User",
                organization="TestOrg",
                password="secure123",
            )

    def test_user_first_name_max_length(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                first_name="a" * 121,
                last_name="User",
                organization="TestOrg",
                password="secure123",
            )

    def test_user_update_partial(self):
        update = UserUpdate(first_name="NewName")
        assert update.first_name == "NewName"
        assert update.email is None


@pytest.mark.unit
class TestAlertModels:
    def test_alert_create_valid(self):
        alert = AlertCreate(
            name="Test Alert",
            descriptors=["python", "fastapi", "api"],
            categories=[{"code": "TECH", "label": "Technology"}],
            cron_expression="0 * * * *",
        )
        assert alert.name == "Test Alert"
        assert len(alert.descriptors) == 3

    def test_alert_response(self):
        alert = Alert(
            id=1,
            user_id=1,
            name="Test Alert",
            descriptors=["python", "fastapi"],
            categories=[],
            cron_expression="0 * * * *",
        )
        assert alert.id == 1
        assert alert.user_id == 1


@pytest.mark.unit
class TestCategoryModels:
    def test_category_create(self):
        cat = CategoryCreate(name="Technology", source="IPTC")
        assert cat.name == "Technology"
        assert cat.source == "IPTC"

    def test_category_invalid_source(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Tech", source="INVALID")


@pytest.mark.unit
class TestNotificationModels:
    def test_notification_create(self):
        from datetime import datetime

        from app.main import Metric

        notif = Notification(
            id=1,
            alert_id=1,
            timestamp=datetime.now(),
            metrics=[Metric(name="count", value=5.0)],
        )
        assert notif.id == 1
        assert len(notif.metrics) == 1


@pytest.mark.unit
class TestInformationSourceModels:
    def test_source_create(self):
        source = InformationSourceCreate(
            name="BBC News",
            url="https://www.bbc.com/news",
        )
        assert source.name == "BBC News"


@pytest.mark.unit
class TestRSSChannelModels:
    def test_channel_create(self):
        channel = RSSChannel(
            id=1,
            information_source_id=1,
            url="https://feeds.bbci.co.uk/news/rss.xml",
            category_id=1,
        )
        assert channel.id == 1
        assert channel.information_source_id == 1
