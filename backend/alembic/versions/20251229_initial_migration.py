"""初始迁移

Revision ID: 001
Revises:
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(200), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # 创建邮箱配置表
    op.create_table(
        'email_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_address', sa.String(200), nullable=False, unique=True),
        sa.Column('auth_code_encrypted', sa.String(500), nullable=False),
        sa.Column('imap_server', sa.String(100), default='imap.exmail.qq.com'),
        sa.Column('imap_port', sa.Integer(), default=993),
        sa.Column('folder', sa.String(100), default='INBOX'),
        sa.Column('processed_folder', sa.String(100), default='已处理'),
        sa.Column('filter_keywords', postgresql.JSONB(), default=list),
        sa.Column('sender_whitelist', postgresql.JSONB(), default=list),
        sa.Column('poll_interval', sa.Integer(), default=300),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 创建岗位表
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('required_skills', postgresql.JSONB(), default=list),
        sa.Column('preferred_skills', postgresql.JSONB(), default=list),
        sa.Column('min_work_years', sa.Integer(), default=0),
        sa.Column('min_education', sa.String(50), default='大专'),
        sa.Column('skill_weight', sa.Integer(), default=50),
        sa.Column('experience_weight', sa.Integer(), default=30),
        sa.Column('education_weight', sa.Integer(), default=20),
        sa.Column('pass_threshold', sa.Integer(), default=70),
        sa.Column('review_threshold', sa.Integer(), default=50),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 创建简历表
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_name', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('education', sa.String(50)),
        sa.Column('work_years', sa.Integer()),
        sa.Column('skills', postgresql.JSONB(), default=list),
        sa.Column('work_experience', postgresql.JSONB(), default=list),
        sa.Column('project_experience', postgresql.JSONB(), default=list),
        sa.Column('education_history', postgresql.JSONB(), default=list),
        sa.Column('raw_text', sa.Text()),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_type', sa.String(20)),
        sa.Column('source_email_id', sa.String(200)),
        sa.Column('source_email_subject', sa.String(500)),
        sa.Column('source_sender', sa.String(200)),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 创建筛选结果表
    op.create_table(
        'screening_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_score', sa.Integer()),
        sa.Column('rule_score', sa.Integer()),
        sa.Column('similarity_score', sa.Numeric(5, 2)),
        sa.Column('skill_score', sa.Integer()),
        sa.Column('experience_score', sa.Integer()),
        sa.Column('education_score', sa.Integer()),
        sa.Column('matched_points', postgresql.JSONB(), default=list),
        sa.Column('unmatched_points', postgresql.JSONB(), default=list),
        sa.Column('match_details', postgresql.JSONB(), default=dict),
        sa.Column('screening_result', sa.String(20)),
        sa.Column('confidence', sa.Numeric(3, 2)),
        sa.Column('suggestion', sa.Text()),
        sa.Column('processing_time_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('resume_id', 'job_id', name='uq_resume_job'),
    )


def downgrade() -> None:
    op.drop_table('screening_results')
    op.drop_table('resumes')
    op.drop_table('jobs')
    op.drop_table('email_configs')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
