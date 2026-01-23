"""add candidate_cities field

Revision ID: 20260119_add_candidate_cities
Revises: 20260105_update_screening_result_fields
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260119_add_candidate_cities'
down_revision = '20260105_update_screening_result_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('resumes', sa.Column(
        'candidate_cities',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
        server_default='[]'
    ))


def downgrade():
    op.drop_column('resumes', 'candidate_cities')
