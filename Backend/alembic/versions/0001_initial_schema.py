"""initial PostgreSQL schema

Revision ID: 0001
Revises:
Create Date: 2026-04-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="IPTC"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)

    op.create_table(
        "information_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
    )
    op.create_index(op.f("ix_information_sources_id"), "information_sources", ["id"], unique=False)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)

    op.create_table(
        "stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("total_news", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_notifications", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )
    op.create_index(op.f("ix_stats_id"), "stats", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("organization", sa.String(length=180), nullable=False),
        sa.Column("password", sa.String(length=128), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("cron_expression", sa.String(length=120), nullable=False),
        sa.Column("descriptors", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column(
            "categories", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("rss_channels_ids", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("information_sources_ids", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)

    op.create_table(
        "rss_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("information_source_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["information_source_id"], ["information_sources.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_rss_channels_id"), "rss_channels", ["id"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("iptc_category", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("user_roles")
    op.drop_index(op.f("ix_rss_channels_id"), table_name="rss_channels")
    op.drop_table("rss_channels")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_stats_id"), table_name="stats")
    op.drop_table("stats")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_information_sources_id"), table_name="information_sources")
    op.drop_table("information_sources")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
