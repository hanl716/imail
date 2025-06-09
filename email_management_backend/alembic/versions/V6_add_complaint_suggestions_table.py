"""Add complaint_suggestions table

Revision ID: v6_complaint_data
Revises: v5_category_email_message
Create Date: 2024-07-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v6_complaint_data'
down_revision: Union[str, None] = 'v5_category_email_message'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('complaint_suggestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('submitter_email', sa.String(), nullable=False),
        sa.Column('submitter_name', sa.String(), nullable=True),
        sa.Column('issue_type', sa.String(length=50), nullable=False),
        sa.Column('category_detail', sa.String(length=100), nullable=True),
        sa.Column('product_service', sa.String(length=100), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('sentiment', sa.String(length=50), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), nullable=True), # Default is handled by model

        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_message_id') # Ensure one-to-one relationship
    )
    op.create_index(op.f('ix_complaint_suggestions_id'), 'complaint_suggestions', ['id'], unique=False)
    op.create_index(op.f('ix_complaint_suggestions_user_id'), 'complaint_suggestions', ['user_id'], unique=False)
    op.create_index(op.f('ix_complaint_suggestions_submitter_email'), 'complaint_suggestions', ['submitter_email'], unique=False)
    op.create_index(op.f('ix_complaint_suggestions_email_message_id'), 'complaint_suggestions', ['email_message_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_complaint_suggestions_email_message_id'), table_name='complaint_suggestions')
    op.drop_index(op.f('ix_complaint_suggestions_submitter_email'), table_name='complaint_suggestions')
    op.drop_index(op.f('ix_complaint_suggestions_user_id'), table_name='complaint_suggestions')
    op.drop_index(op.f('ix_complaint_suggestions_id'), table_name='complaint_suggestions')
    op.drop_table('complaint_suggestions')
