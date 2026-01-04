"""add agent config fields to jobs

Revision ID: 20260104_add_agent_config_fields
Revises: 20251231_add_education_level
Create Date: 2026-01-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260104_add_agent_config_fields'
down_revision = '20251231_add_education_level'
branch_labels = None
depends_on = None


def upgrade():
    """添加Agent配置字段到jobs表"""
    op.add_column('jobs', sa.Column('agent_type', sa.String(length=20), nullable=True, server_default='http'))
    op.add_column('jobs', sa.Column('agent_url', sa.String(length=500), nullable=True))
    op.add_column('jobs', sa.Column('agent_timeout', sa.Integer(), nullable=True, server_default='30'))
    op.add_column('jobs', sa.Column('agent_retry', sa.Integer(), nullable=True, server_default='3'))


def downgrade():
    """移除Agent配置字段"""
    op.drop_column('jobs', 'agent_retry')
    op.drop_column('jobs', 'agent_timeout')
    op.drop_column('jobs', 'agent_url')
    op.drop_column('jobs', 'agent_type')
