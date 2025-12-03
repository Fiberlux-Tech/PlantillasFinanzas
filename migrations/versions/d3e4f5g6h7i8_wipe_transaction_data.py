"""Wipe all data from transaction-related tables

Revision ID: d3e4f5g6h7i8
Revises: c1d2e3f4g5h6
Create Date: 2025-12-03 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3e4f5g6h7i8'
down_revision = 'c1d2e3f4g5h6'
branch_labels = None
depends_on = None


def upgrade():
    # Delete in correct order: children first, then parent
    # This respects foreign key constraints

    # 1. Delete all recurring services (child table)
    op.execute('DELETE FROM recurring_service;')

    # 2. Delete all fixed costs (child table)
    op.execute('DELETE FROM fixed_cost;')

    # 3. Delete all transactions (parent table)
    op.execute('DELETE FROM transaction;')


def downgrade():
    # Cannot restore deleted data
    # This is a destructive operation with no reversal
    pass
