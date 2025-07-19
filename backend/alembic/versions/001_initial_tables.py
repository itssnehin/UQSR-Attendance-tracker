"""Create initial tables

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create runs table
    op.create_table('runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_runs_id'), 'runs', ['id'], unique=False)
    op.create_index(op.f('ix_runs_date'), 'runs', ['date'], unique=True)
    op.create_index(op.f('ix_runs_session_id'), 'runs', ['session_id'], unique=True)

    # Create calendar_config table
    op.create_table('calendar_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('has_run', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_config_id'), 'calendar_config', ['id'], unique=False)
    op.create_index(op.f('ix_calendar_config_date'), 'calendar_config', ['date'], unique=True)

    # Create attendances table
    op.create_table('attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('runner_name', sa.String(length=255), nullable=False),
        sa.Column('registered_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id', 'runner_name', name='uq_attendances_run_runner')
    )
    op.create_index(op.f('ix_attendances_id'), 'attendances', ['id'], unique=False)
    op.create_index(op.f('ix_attendances_run_id'), 'attendances', ['run_id'], unique=False)
    op.create_index(op.f('ix_attendances_runner_name'), 'attendances', ['runner_name'], unique=False)


def downgrade() -> None:
    op.drop_table('attendances')
    op.drop_table('calendar_config')
    op.drop_table('runs')