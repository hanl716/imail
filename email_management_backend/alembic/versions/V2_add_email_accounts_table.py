"""Add email_accounts table

Revision ID: v2_email_accounts_table
Revises: v1_users_table
Create Date: 2024-07-05 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v2_email_accounts_table'
down_revision: Union[str, None] = 'v1_users_table' # Points to the users table migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('email_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_address', sa.String(), nullable=False),
        sa.Column('imap_server', sa.String(), nullable=True),
        sa.Column('imap_port', sa.Integer(), nullable=True),
        sa.Column('smtp_server', sa.String(), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True),
        sa.Column('email_user', sa.String(), nullable=True),
        sa.Column('encrypted_password', sa.LargeBinary(), nullable=True),
        sa.Column('encrypted_access_token', sa.LargeBinary(), nullable=True),
        sa.Column('encrypted_refresh_token', sa.LargeBinary(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Standard Alembic naming for index is ix_<table>_<column>.
    # op.f() is a helper for this but can be written directly.
    op.create_index('ix_email_accounts_email_address', 'email_accounts', ['email_address'], unique=False)
    op.create_index('ix_email_accounts_id', 'email_accounts', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_email_accounts_id', table_name='email_accounts')
    op.drop_index('ix_email_accounts_email_address', table_name='email_accounts')
    op.drop_table('email_accounts')
