"""add rbac user job categories

Revision ID: 20260123_add_rbac
Revises: 20260122_remove_processed_folder
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260123_add_rbac'
down_revision = '20260122_remove_processed_folder'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 user_job_categories 表
    op.create_table(
        'user_job_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_category_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'job_category_name', name='uq_user_job_category')
    )
    # 创建索引用于更快查询
    op.create_index('ix_user_job_categories_user_id', 'user_job_categories', ['user_id'])


def downgrade():
    op.drop_index('ix_user_job_categories_user_id', table_name='user_job_categories')
    op.drop_table('user_job_categories')
