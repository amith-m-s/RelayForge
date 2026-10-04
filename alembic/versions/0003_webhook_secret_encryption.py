"""Prepare webhook secret encryption with safe rotation.

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
    op.add_column(
        "webhook_endpoints",
        sa.Column("secret_encrypted", sa.Text(), nullable=True),
    )
    # Existing secret_hash values are one-way hashes and cannot be converted
    # into the original signing secret. Require explicit secret rotation.
    op.execute(
        "UPDATE webhook_endpoints SET status='disabled' "
        "WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.drop_column("webhook_endpoints", "secret_encrypted")
