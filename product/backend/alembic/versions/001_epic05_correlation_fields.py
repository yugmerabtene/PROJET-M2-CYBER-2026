"""EPIC-05 Add correlation score and attack chain fields

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-05-08 12:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to correlation_groups
    op.add_column('correlation_groups', sa.Column('correlation_score', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('correlation_groups', sa.Column('hostname', sa.String(255), nullable=True))
    op.add_column('correlation_groups', sa.Column('ip_cidr', sa.String(20), nullable=True))
    op.add_column('correlation_groups', sa.Column('attack_chain_type', sa.String(64), nullable=True))
    op.add_column('correlation_groups', sa.Column('score_breakdown', sa.JSON(), nullable=True))
    
    # Add new columns to correlated_events
    op.add_column('correlated_events', sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('correlated_events', sa.Column('ml_anomaly_score', sa.Float(), nullable=False, server_default='0.0'))
    
    # Create alert_correlation_assoc table
    op.create_table(
        'alert_correlation_assoc',
        sa.Column('alert_id', sa.Integer(), sa.ForeignKey('alerts.id'), primary_key=True),
        sa.Column('correlation_group_id', sa.Integer(), sa.ForeignKey('correlation_groups.id'), primary_key=True),
        sa.Column('linked_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_correlation_groups_correlation_score', 'correlation_groups', ['correlation_score'])
    op.create_index('ix_correlation_groups_hostname', 'correlation_groups', ['hostname'])
    op.create_index('ix_correlation_groups_ip_cidr', 'correlation_groups', ['ip_cidr'])
    op.create_index('ix_correlated_events_sequence_order', 'correlated_events', ['sequence_order'])


def downgrade() -> None:
    op.drop_index('ix_correlated_events_sequence_order')
    op.drop_index('ix_correlation_groups_ip_cidr')
    op.drop_index('ix_correlation_groups_hostname')
    op.drop_index('ix_correlation_groups_correlation_score')
    op.drop_table('alert_correlation_assoc')
    op.drop_column('correlated_events', 'ml_anomaly_score')
    op.drop_column('correlated_events', 'sequence_order')
    op.drop_column('correlation_groups', 'score_breakdown')
    op.drop_column('correlation_groups', 'attack_chain_type')
    op.drop_column('correlation_groups', 'ip_cidr')
    op.drop_column('correlation_groups', 'hostname')
    op.drop_column('correlation_groups', 'correlation_score')
