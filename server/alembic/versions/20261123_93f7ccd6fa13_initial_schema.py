"""initial schema

Revision ID: 93f7ccd6fa13
Revises:
Create Date: 2026-11-23 20:23:55.018572

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "93f7ccd6fa13"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_failures",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=254), nullable=False),
        sa.Column(
            "failed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auth_failures_failed_at"), "auth_failures", ["failed_at"], unique=False
    )
    op.create_index(op.f("ix_auth_failures_key"), "auth_failures", ["key"], unique=False)
    op.create_table(
        "operators",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("subject", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("event", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("nominee", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pin_hash", sa.String(length=255), nullable=False),
        sa.Column("owner_operator_id", sa.String(length=32), nullable=True),
        sa.Column("scenario_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_operator_id"], ["operators.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        op.f("ix_cases_owner_operator_id"), "cases", ["owner_operator_id"], unique=False
    )
    op.create_table(
        "case_tokens",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(op.f("ix_case_tokens_case_id"), "case_tokens", ["case_id"], unique=False)
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("case_id", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_case_id"), "documents", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_case_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_case_tokens_case_id"), table_name="case_tokens")
    op.drop_table("case_tokens")
    op.drop_index(op.f("ix_cases_owner_operator_id"), table_name="cases")
    op.drop_table("cases")
    op.drop_table("operators")
    op.drop_index(op.f("ix_auth_failures_key"), table_name="auth_failures")
    op.drop_index(op.f("ix_auth_failures_failed_at"), table_name="auth_failures")
    op.drop_table("auth_failures")
