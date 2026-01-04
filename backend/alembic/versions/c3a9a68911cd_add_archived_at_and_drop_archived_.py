"""add archived_at and drop archived boolean

Revision ID: c3a9a68911cd
Revises: 47f5d4737325
Create Date: 2026-01-03 22:51:18.167399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a9a68911cd'
down_revision: Union[str, None] = '47f5d4737325'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add archived_at column, backfill existing archived values, and drop archived boolean."""
    # Add archived_at column as nullable
    op.add_column('values', 
        sa.Column('archived_at', sa.DateTime(), nullable=True))
    
    # Backfill existing archived values with current timestamp
    # This ensures no NULL archived_at for archived values
    op.execute("""
        UPDATE values 
        SET archived_at = CURRENT_TIMESTAMP 
        WHERE archived = true
    """)
    
    # Drop the old archived boolean column
    op.drop_column('values', 'archived')


def downgrade() -> None:
    """Restore archived boolean column from archived_at."""
    # Add back archived boolean column with default
    op.add_column('values',
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'))
    
    # Backfill: if archived_at is set, mark as archived
    op.execute("""
        UPDATE values
        SET archived = true
        WHERE archived_at IS NOT NULL
    """)
    
    # Drop archived_at column
    op.drop_column('values', 'archived_at')
