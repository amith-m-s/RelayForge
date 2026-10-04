"""Enforce tenant-scoped event idempotency for active records.

Revision ID: 0002_event_idempotency
Revises: 0001_initial
"""
from alembic import op

revision = "0002_event_idempotency"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX uq_events_org_idempotency_active
        ON events (organization_id, idempotency_key)
        WHERE idempotency_key IS NOT NULL AND deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("uq_events_org_idempotency_active", table_name="events")
