from alembic import op
import sqlalchemy as sa

revision = "kb_vector_001"
down_revision = "b1c39b2569a6"
branch_labels = None
depends_on = None

def upgrade():
    # Remove vector extension and table creation as we're no longer using embeddings
    pass

def downgrade():
    # Remove vector extension and table drop as we're no longer using embeddings
    pass
