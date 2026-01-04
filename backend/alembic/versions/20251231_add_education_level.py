"""add education_level field

Revision ID: 20251231_add_education_level
Revises: 20251231_add_city_agent_pdf_fields
Create Date: 2025-12-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251231_add_education_level'
down_revision = '002_add_city_agent'
branch_labels = None
depends_on = None


def upgrade():
    """添加education_level字段到resumes表"""
    op.add_column('resumes', sa.Column('education_level', sa.String(20), nullable=True))


def downgrade():
    """移除education_level字段"""
    op.drop_column('resumes', 'education_level')
