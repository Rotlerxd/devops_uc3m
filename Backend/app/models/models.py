from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

# Tabla de asociación Muchos-a-Muchos para Usuarios y Roles
user_role_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    users: Mapped[list[User]] = relationship("User", secondary=user_role_table, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    organization: Mapped[str] = mapped_column(String(180), nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    roles: Mapped[list[Role]] = relationship("Role", secondary=user_role_table, back_populates="users")
    alerts: Mapped[list[Alert]] = relationship("Alert", back_populates="user", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(120), nullable=False)
    descriptors: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    categories: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    rss_channels_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    information_sources_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    user: Mapped[User] = relationship("User", back_populates="alerts")
    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="alert", cascade="all, delete-orphan"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    iptc_category: Mapped[str] = mapped_column(String, nullable=False)

    alert: Mapped[Alert] = relationship("Alert", back_populates="notifications")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String, default="IPTC", nullable=False)

    channels: Mapped[list[RSSChannel]] = relationship("RSSChannel", back_populates="category")


class InformationSource(Base):
    __tablename__ = "information_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    channels: Mapped[list[RSSChannel]] = relationship(
        "RSSChannel", back_populates="source", cascade="all, delete-orphan"
    )


class RSSChannel(Base):
    __tablename__ = "rss_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    information_source_id: Mapped[int] = mapped_column(
        ForeignKey("information_sources.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    source: Mapped[InformationSource] = relationship("InformationSource", back_populates="channels")
    category: Mapped[Category] = relationship("Category", back_populates="channels")


class Stats(Base):
    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    total_news: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_notifications: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metrics: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
