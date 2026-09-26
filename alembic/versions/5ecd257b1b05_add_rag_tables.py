"""add rag tables

Revision ID: 5ecd257b1b05
Revises: 90ec84f07dff
Create Date: 2026-09-25 22:00:46.612629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector 


# revision identifiers, used by Alembic.
revision: str = '5ecd257b1b05'
down_revision: Union[str, Sequence[str], None] = '90ec84f07dff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                   sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="note"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(),
                   sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(),
                   sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
    )

    # Full-text search column, kept in sync by trigger.
    op.execute("ALTER TABLE document_chunks ADD COLUMN tsv tsvector")
    op.execute("""
        CREATE OR REPLACE FUNCTION document_chunks_tsv_update() RETURNS trigger AS $$
        BEGIN
            NEW.tsv :=
                setweight(to_tsvector('english', coalesce(NEW.content, '')), 'A') ||
                setweight(to_tsvector('english',
                    coalesce((SELECT title FROM documents WHERE id = NEW.document_id), '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_document_chunks_tsv
        BEFORE INSERT OR UPDATE OF content, document_id ON document_chunks
        FOR EACH ROW EXECUTE FUNCTION document_chunks_tsv_update()
    """)

    op.create_index("ix_document_chunks_user", "document_chunks", ["user_id"])
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_tsv_gin ON document_chunks USING gin (tsv)"
    )


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_document_chunks_tsv ON document_chunks")
    op.execute("DROP FUNCTION IF EXISTS document_chunks_tsv_update()")
    op.drop_index("ix_document_chunks_tsv_gin", table_name="document_chunks")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_index("ix_document_chunks_user", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("documents")