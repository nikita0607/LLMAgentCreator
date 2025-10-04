"""Remove embeddings table

Revision ID: 20251002_remove_embeddings
Revises: 20250930_add_last_user_input
Create Date: 2025-10-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251002_remove_embeddings'
down_revision = '20250930_add_last_user_input'
branch_labels = None
depends_on = None

def upgrade():
    # Drop the knowledge_embeddings table
    op.drop_table('knowledge_embeddings')

def downgrade():
    # Recreate the knowledge_embeddings table
    op.create_table(
        'knowledge_embeddings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('kb_id', sa.Integer(), sa.ForeignKey('knowledge_node.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),  # Store as text since we don't have pgvector in downgrade
        sa.Column('text_chunk', sa.Text(), nullable=False),
    )