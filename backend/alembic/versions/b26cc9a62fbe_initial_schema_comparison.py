"""initial schema comparison

Revision ID: b26cc9a62fbe
Revises: 
Create Date: 2026-11-16 20:27:36.481932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b26cc9a62fbe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_index(
        "uq_active_emergency_per_incident",
        "emergency_records",
        ["incident_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending_owner_approval', 'approved_pending_delivery')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_active_emergency_per_incident",
        table_name="emergency_records",
        postgresql_where=sa.text(
            "status IN ('pending_owner_approval', 'approved_pending_delivery')"
        ),
    )