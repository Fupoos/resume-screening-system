"""add agent parsing fields and agent parsing history table

Revision ID: 20260202_agent_parsing
Revises: 20260123_add_rbac
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260202_agent_parsing'
down_revision = '20260123_add_rbac'
branch_labels = None
depends_on = None


def upgrade():
    # ==================== Resume 表新增字段 ====================
    # Agent解析相关字段
    op.add_column('resumes', sa.Column('parsed_by_agent', sa.String(20), server_default='local', nullable=False))
    op.add_column('resumes', sa.Column('agent_parsed_at', sa.DateTime(), nullable=True))
    op.add_column('resumes', sa.Column('agent_parsed_data', postgresql.JSONB(), nullable=True))
    op.add_column('resumes', sa.Column('job_title_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('resumes', sa.Column('parsing_agent_version', sa.String(50), nullable=True))
    op.add_column('resumes', sa.Column('parse_success', sa.Boolean(), server_default='true', nullable=True))
    op.add_column('resumes', sa.Column('parse_error_message', sa.Text(), nullable=True))

    # 为 parsed_by_agent 列添加索引（用于筛选查询）
    op.create_index('ix_resumes_parsed_by_agent', 'resumes', ['parsed_by_agent'])

    # ==================== Job 表新增字段 ====================
    # 评分Agent专用配置
    op.add_column('jobs', sa.Column('scoring_agent_api_key', sa.String(200), nullable=True))
    op.add_column('jobs', sa.Column('scoring_agent_url', sa.String(500), nullable=True))
    op.add_column('jobs', sa.Column('is_scoring_active', sa.Boolean(), server_default='true', nullable=True))

    # ==================== 创建 agent_parsing_history 表 ====================
    op.create_table(
        'agent_parsing_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_type', sa.String(50), server_default='fastgpt', nullable=True),
        sa.Column('agent_version', sa.String(50), nullable=True),
        sa.Column('request_payload', postgresql.JSONB(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(), nullable=True),
        sa.Column('parsed_candidate_name', sa.String(100), nullable=True),
        sa.Column('parsed_job_title', sa.String(100), nullable=True),
        sa.Column('job_confidence', sa.Integer(), nullable=True),
        sa.Column('parsing_success', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 创建索引用于更快查询
    op.create_index('ix_agent_parsing_history_resume_id', 'agent_parsing_history', ['resume_id'])
    op.create_index('ix_agent_parsing_history_created_at', 'agent_parsing_history', ['created_at'])
    op.create_index('ix_agent_parsing_history_parsing_success', 'agent_parsing_history', ['parsing_success'])


def downgrade():
    # 删除索引
    op.drop_index('ix_agent_parsing_history_parsing_success', table_name='agent_parsing_history')
    op.drop_index('ix_agent_parsing_history_created_at', table_name='agent_parsing_history')
    op.drop_index('ix_agent_parsing_history_resume_id', table_name='agent_parsing_history')

    # 删除 agent_parsing_history 表
    op.drop_table('agent_parsing_history')

    # 删除 Job 表字段
    op.drop_column('jobs', 'is_scoring_active')
    op.drop_column('jobs', 'scoring_agent_url')
    op.drop_column('jobs', 'scoring_agent_api_key')

    # 删除 Resume 表索引和字段
    op.drop_index('ix_resumes_parsed_by_agent', table_name='resumes')
    op.drop_column('resumes', 'parse_error_message')
    op.drop_column('resumes', 'parse_success')
    op.drop_column('resumes', 'parsing_agent_version')
    op.drop_column('resumes', 'job_title_confidence')
    op.drop_column('resumes', 'agent_parsed_data')
    op.drop_column('resumes', 'agent_parsed_at')
    op.drop_column('resumes', 'parsed_by_agent')
