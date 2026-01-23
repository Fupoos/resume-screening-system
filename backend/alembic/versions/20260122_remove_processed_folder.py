"""remove processed_folder field

Revision ID: 20260122_remove_processed_folder
Revises: 20260119_add_candidate_cities
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260122_remove_processed_folder'
down_revision = '20260119_add_candidate_cities'
branch_labels = None
depends_on = None


def upgrade():
    # 删除 email_configs 表中的 processed_folder 字段
    op.drop_column('email_configs', 'processed_folder')


def downgrade():
    # 恢复 processed_folder 字段
    op.add_column('email_configs', sa.Column('processed_folder', sa.String(100), nullable=True, server_default='已处理'))
