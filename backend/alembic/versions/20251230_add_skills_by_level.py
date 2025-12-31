"""add skills_by_level to resumes

Revision ID: 20251230_add_skills_by_level
Revises: 20251229_initial_migration
Create Date: 2025-12-30 15:44:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251230_add_skills_by_level'
down_revision = '001'  # 修复：引用第一个迁移的实际revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Add skills_by_level column as JSONB
    op.add_column(
        'resumes',
        sa.Column(
            'skills_by_level',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True
        )
    )


def downgrade():
    # Remove skills_by_level column
    op.drop_column('resumes', 'skills_by_level')
