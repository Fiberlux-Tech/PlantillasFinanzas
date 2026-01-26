"""Remove password_hash from User model (Supabase handles auth)

Revision ID: 002_rm_pwd_hash
Revises: 001_migrate_user_id
Create Date: 2025-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_rm_pwd_hash'
down_revision = '001_migrate_user_id'
branch_labels = None
depends_on = None


def upgrade():
    """
    Removes the password_hash column from the User table.

    Supabase handles authentication, so password storage in the
    application database is no longer needed.
    """
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password_hash')


def downgrade():
    """
    Re-adds the password_hash column to the User table.

    WARNING: This will create an empty password_hash column.
    Users will need to reset their passwords.
    """
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=256), nullable=True))
