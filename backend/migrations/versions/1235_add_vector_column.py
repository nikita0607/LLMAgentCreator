from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "kb_vector_001"
down_revision = "b1c39b2569a6"
branch_labels = None
depends_on = None

def upgrade():
    # на всякий случай создадим расширение в этой БД
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.drop_table("knowledge_embeddings")
    op.create_table(
        "knowledge_embeddings",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("kb_id", sa.Integer, sa.ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("text_chunk", sa.Text, nullable=False),
    )

def downgrade():
    op.drop_table("knowledge_embeddings")
