"""Initial schema.

Revision ID: 20260213_0001
Revises:
Create Date: 2026-02-13 16:30:00
"""

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260213_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "tables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("end_at > start_at", name="ck_bookings_end_after_start"),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bookings_table_interval",
        "bookings",
        ["table_id", "start_at", "end_at"],
        unique=False,
    )
    op.create_index("ix_bookings_user_start", "bookings", ["user_id", "start_at"], unique=False)

    default_tables = sa.table(
        "tables",
        sa.column("name", sa.String),
        sa.column("seats", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    created_at = datetime.now(tz=timezone.utc)
    rows: list[dict[str, object]] = []
    for seats, count in ((2, 7), (3, 6), (6, 3)):
        for position in range(1, count + 1):
            rows.append({"name": f"T{seats}-{position}", "seats": seats, "created_at": created_at})
    op.bulk_insert(default_tables, rows)


def downgrade() -> None:
    op.drop_index("ix_bookings_user_start", table_name="bookings")
    op.drop_index("ix_bookings_table_interval", table_name="bookings")
    op.drop_table("bookings")
    op.drop_table("tables")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
