"""add city, agent score, pdf fields

Revision ID: 002_add_city_agent
Revises: 20251230_add_skills_by_level
Create Date: 2025-12-30 17:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_city_agent'
down_revision = '20251230_add_skills_by_level'
branch_labels = None
depends_on = None


def upgrade():
    # 添加地理和分类信息字段
    op.add_column('resumes', sa.Column('city', sa.String(length=50), nullable=True))
    op.add_column('resumes', sa.Column('job_category', sa.String(length=20), nullable=True))

    # 添加PDF相关字段
    op.add_column('resumes', sa.Column('pdf_path', sa.String(length=500), nullable=True))

    # 添加Agent评估结果字段
    op.add_column('resumes', sa.Column('agent_score', sa.Integer(), nullable=True))
    op.add_column('resumes', sa.Column('agent_evaluation_id', sa.String(length=100), nullable=True))
    op.add_column('resumes', sa.Column('agent_evaluated_at', sa.DateTime(), nullable=True))

    # 添加筛选结果字段
    op.add_column('resumes', sa.Column('screening_status', sa.String(length=20), server_default='pending', nullable=True))


def downgrade():
    # 删除字段
    op.drop_column('resumes', 'screening_status')
    op.drop_column('resumes', 'agent_evaluated_at')
    op.drop_column('resumes', 'agent_evaluation_id')
    op.drop_column('resumes', 'agent_score')
    op.drop_column('resumes', 'pdf_path')
    op.drop_column('resumes', 'job_category')
    op.drop_column('resumes', 'city')
