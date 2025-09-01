"""add knowledge_base and knowledge_embeddings

Revision ID: kb_001
Revises:
Create Date: 2025-09-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'kb_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Таблица knowledge_base
    op.create_table(
        'knowledge_base',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('agent_id', sa.Integer, sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('type', sa.String, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # Таблица knowledge_embeddings
    op.create_table(
        'knowledge_embeddings',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('kb_id', sa.Integer, sa.ForeignKey('knowledge_base.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float, dimensions=1), nullable=False),  # массив float вместо VECTOR
        sa.Column('text_chunk', sa.Text, nullable=False),
    )


def downgrade():
    op.drop_table('knowledge_embeddings')
    op.drop_table('knowledge_base')
