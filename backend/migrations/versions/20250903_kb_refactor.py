"""remove knowledge_base, link embeddings directly to node

Revision ID: 20250903_kb_refactor
Revises: <previous_revision>
Create Date: 2025-09-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250903_kb_refactor'
down_revision = 'kb_vector_001'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Создаём таблицу knowledge_node (если ещё нет)
    op.create_table(
        'knowledge_node',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('agent_id', sa.Integer, sa.ForeignKey('agent.id', ondelete='CASCADE')),
        sa.Column('node_id', sa.String, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('source_type', sa.String, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # 2. Добавляем столбец node_id в knowledge_embeddings
    op.add_column('knowledge_embeddings', sa.Column('node_id', sa.Integer(), nullable=True))

    # 3. Создаём FK на knowledge_node
    op.create_foreign_key(
        'fk_embeddings_node',
        'knowledge_embeddings', 'knowledge_node',
        ['node_id'], ['id'],
        ondelete='CASCADE'
    )

    # 4. Удаляем таблицу knowledge_base вместе с зависимостями
    op.execute('DROP TABLE knowledge_base CASCADE;')


def downgrade():
    # 1. Восстанавливаем knowledge_base (пустая)
    op.create_table(
        'knowledge_base',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('node_id', sa.Integer, sa.ForeignKey('knowledge_node.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now())
    )

    # 2. Удаляем FK и столбец node_id из embeddings
    op.drop_constraint('fk_embeddings_node', 'knowledge_embeddings', type_='foreignkey')
    op.drop_column('knowledge_embeddings', 'node_id')

    # 3. Удаляем таблицу knowledge_node
    op.drop_table('knowledge_node')
