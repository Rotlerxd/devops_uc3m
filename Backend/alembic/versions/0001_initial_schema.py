"""initial schema — usuarios table

Revision ID: 0001
Revises:
Create Date: 2026-03-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("apellidos", sa.String(), nullable=False),
        sa.Column("organizacion", sa.String(), nullable=True),
        sa.Column(
            "rol",
            sa.Enum("gestor", "lector", name="rolusuario", native_enum=False, length=50),
            server_default="lector",
        ),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_table("usuarios")
