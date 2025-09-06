"""change node_id to string in knowledge_embeddings"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "20230903_change_node_id_string"
down_revision = "20250903_kb_refactor"
branch_labels = None
depends_on = None


def upgrade():
    # Удаляем старый FK, если был
    with op.batch_alter_table("knowledge_embeddings") as batch_op:
        batch_op.drop_constraint("fk_embeddings_node", type_="foreignkey")
        batch_op.alter_column(
            "node_id",
            existing_type=sa.String(),
            type_=sa.Integer(),
            existing_nullable=False
        )
        batch_op.create_foreign_key(
            "fk_embeddings_node",
            "knowledge_node",
            ["node_id"], ["id"],
            ondelete="CASCADE"
        )


def downgrade():
    with op.batch_alter_table("knowledge_embeddings") as batch_op:
        batch_op.drop_constraint("fk_embeddings_node", type_="foreignkey")
        batch_op.alter_column(
            "node_id",
            existing_type=sa.Integer(),
            type_=sa.String(),
            existing_nullable=False
        )
        batch_op.create_foreign_key(
            "fk_embeddings_node",
            "knowledge_node",
            ["node_id"], ["id"],
            ondelete="CASCADE"
        )
