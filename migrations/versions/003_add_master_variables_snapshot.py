"""Add master_variables_snapshot column for frozen rate audit trail

Revision ID: 003_add_master_variables_snapshot
Revises: 002_remove_password_hash
Create Date: 2026-01-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_master_variables_snapshot'
down_revision = '002_remove_password_hash'
branch_labels = None
depends_on = None


def upgrade():
    """
    Adds master_variables_snapshot JSON column to Transaction table.

    This column stores the MasterVariables (tipoCambio, costoCapital, tasaCartaFianza)
    frozen at transaction creation time, ensuring immutability for audit purposes.
    """
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('master_variables_snapshot', sa.JSON(), nullable=True))


def downgrade():
    """
    Removes master_variables_snapshot column from Transaction table.
    """
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('master_variables_snapshot')
