"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('location', sa.String(255)),
        sa.Column('budget', sa.Numeric(15, 2)),
        sa.Column('planned_start_date', sa.Date),
        sa.Column('planned_end_date', sa.Date),
        sa.Column('actual_end_date', sa.Date),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_projects_name', 'projects', ['name'])

    op.create_table(
        'vendors',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact_person', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('sla_days', sa.Integer),
        sa.Column('rating', sa.Numeric(3, 2)),
        sa.Column('active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_vendors_name', 'vendors', ['name'])

    op.create_table(
        'materials',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=False), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('unit', sa.String(50)),
        sa.Column('planned_quantity', sa.Numeric(12, 2)),
        sa.Column('actual_quantity', sa.Numeric(12, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'purchase_orders',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('po_number', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', UUID(as_uuid=False), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('vendor_id', UUID(as_uuid=False), sa.ForeignKey('vendors.id'), nullable=False),
        sa.Column('material_id', UUID(as_uuid=False), sa.ForeignKey('materials.id'), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 2)),
        sa.Column('unit_price', sa.Numeric(12, 2)),
        sa.Column('total_price', sa.Numeric(15, 2)),
        sa.Column('expected_delivery', sa.Date),
        sa.Column('approval_status', sa.String(50), server_default='pending'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'shipments',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('shipment_number', sa.String(100), nullable=False, unique=True),
        sa.Column('purchase_order_id', UUID(as_uuid=False), sa.ForeignKey('purchase_orders.id'), nullable=False),
        sa.Column('vendor_id', UUID(as_uuid=False), sa.ForeignKey('vendors.id'), nullable=False),
        sa.Column('origin', sa.String(255)),
        sa.Column('destination', sa.String(255)),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('planned_delivery', sa.Date),
        sa.Column('actual_delivery', sa.Date),
        sa.Column('delay_days', sa.Integer, server_default='0'),
        sa.Column('tracking_reference', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=False), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('file_path', sa.Text),
        sa.Column('content', sa.Text),
        sa.Column('uploaded_by', sa.String(255)),
        sa.Column('uploaded_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('embedding_status', sa.String(50), server_default='pending'),
    )

    op.create_table(
        'ai_analyses',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=False), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('analysis_type', sa.String(100), nullable=False),
        sa.Column('risk_score', sa.Numeric(5, 2)),
        sa.Column('summary', sa.Text),
        sa.Column('recommendation', sa.Text),
        sa.Column('evidence', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('ai_analyses')
    op.drop_table('documents')
    op.drop_table('shipments')
    op.drop_table('purchase_orders')
    op.drop_table('materials')
    op.drop_table('vendors')
    op.drop_table('projects')
