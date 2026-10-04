"""Encrypt stored webhook signing secrets.

Revision ID: 0003_webhook_secret_encryption
Revises: 0002_event_idempotency
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_webhook_secret_encryption"
down_revision = "0002_event_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "webhook_endpoints",
        "secret_hash",
        new_column_name="secret_encrypted",
        existing_type=sa.String(length=64),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.execute(
        "UPDATE webhook_endpoints SET status='disabled' "
        "WHERE secret_encrypted IS NOT NULL"
    )


def downgrade() -> None:
    op.alter_column(
        "webhook_endpoints",
        "secret_encrypted",
        new_column_name="secret_hash",
        existing_type=sa.Text(),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
