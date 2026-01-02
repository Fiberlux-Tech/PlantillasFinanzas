"""Migrate User.id from Integer to String for Supabase UUID

Revision ID: 001_migrate_user_id
Revises: 9fccfb87603f
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_migrate_user_id'
down_revision = '9fccfb87603f'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrates User.id from Integer to String(36) to support Supabase UUIDs.

    Migration strategy:
    1. Drop foreign key constraint on MasterVariable.user_id
    2. Change User.id to String(36)
    3. Change MasterVariable.user_id to String(36)
    4. Recreate foreign key constraint
    """
    # Step 1: Drop foreign key constraint from MasterVariable
    with op.batch_alter_table('master_variable', schema=None) as batch_op:
        batch_op.drop_constraint('master_variable_user_id_fkey', type_='foreignkey')

    # Step 2: Change User.id from Integer to String(36)
    with op.batch_alter_table('user', schema=None) as batch_op:
        # For PostgreSQL: Use ALTER TYPE with USING clause to convert Integer to Text
        batch_op.alter_column('id',
                              existing_type=sa.Integer(),
                              type_=sa.String(length=36),
                              existing_nullable=False,
                              postgresql_using='id::text')

    # Step 3: Change MasterVariable.user_id from Integer to String(36)
    with op.batch_alter_table('master_variable', schema=None) as batch_op:
        batch_op.alter_column('user_id',
                              existing_type=sa.Integer(),
                              type_=sa.String(length=36),
                              existing_nullable=True,
                              postgresql_using='user_id::text')

    # Step 4: Recreate foreign key constraint
    with op.batch_alter_table('master_variable', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'master_variable_user_id_fkey',
            'user', ['user_id'], ['id']
        )


def downgrade():
    """
    Reverts User.id back to Integer from String.

    WARNING: This will fail if there are UUID strings in the database
    that cannot be converted to integers.
    """
    # Step 1: Drop foreign key constraint
    with op.batch_alter_table('master_variable', schema=None) as batch_op:
        batch_op.drop_constraint('master_variable_user_id_fkey', type_='foreignkey')

    # Step 2: Revert User.id to Integer
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('id',
                              existing_type=sa.String(length=36),
                              type_=sa.Integer(),
                              existing_nullable=False,
                              postgresql_using='id::integer')

    # Step 3: Revert MasterVariable.user_id to Integer
    with op.batch_alter_table('master_variable', schema=None) as batch_op:
        batch_op.alter_column('user_id',
                              existing_type=sa.String(length=36),
                              type_=sa.Integer(),
                              existing_nullable=True,
                              postgresql_using='user_id::integer')

    # Step 4: Recreate foreign key constraint
    with op.batch_alter_table('master_variable', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'master_variable_user_id_fkey',
            'user', ['user_id'], ['id']
        )
