"""Remove node_id and enforce kb_id NOT NULL"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '20250903_fix_embeddings'
down_revision = '20230903_change_node_id_string'
branch_labels = None
depends_on = None


def upgrade():
    # Удаляем лишний столбец
    op.drop_column('knowledge_embeddings', 'node_id')

    # Делаем kb_id обязательным
    op.alter_column('knowledge_embeddings', 'kb_id',
                    existing_type=sa.Integer(),
                    nullable=False)

    # Создаём индекс для ускорения поиска
    op.create_index('idx_knowledge_embeddings_kb_id', 'knowledge_embeddings', ['kb_id'])


def downgrade():
    # Откат: добавляем node_id обратно (nullable)
    op.add_column('knowledge_embeddings', sa.Column('node_id', sa.Integer(), nullable=True))

    # Делаем kb_id nullable
    op.alter_column('knowledge_embeddings', 'kb_id',
                    existing_type=sa.Integer(),
                    nullable=True)

    # Удаляем индекс
    op.drop_index('idx_knowledge_embeddings_kb_id', table_name='knowledge_embeddings')
