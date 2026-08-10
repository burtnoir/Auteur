"""Add Project Versioning

Revision ID: 86314a8f0dc1
Revises: c8d8fa2785d6
Create Date: 2026-08-08 18:03:03.147023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86314a8f0dc1'
down_revision = 'c8d8fa2785d6'
branch_labels = None
depends_on = None


def upgrade():
    # --- checkpoint ---------------------------------------------------
    op.create_table(
        'checkpoint',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('label', sa.String(length=120), nullable=False),
        sa.Column('created_date', sa.DateTime(), nullable=False),
    )

    # --- checkpoint_section ---------------------------------------------
    op.create_table(
        'checkpoint_section',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('checkpoint_id', sa.Integer(), sa.ForeignKey('checkpoint.id'), nullable=False),
        sa.Column('structure_id', sa.Integer(), sa.ForeignKey('structure.id'), nullable=False),
        sa.Column('title', sa.String(length=80), nullable=False),
        sa.Column('section_body', sa.Text(), nullable=False),
        sa.Column('synopsis_body', sa.Text(), nullable=False),
        sa.Column('notes_body', sa.Text(), nullable=False),
        sa.Column('characters_body', sa.Text(), nullable=False),
    )
    op.create_index(
        'ix_checkpoint_section_checkpoint_id',
        'checkpoint_section',
        ['checkpoint_id'],
    )

    # --- version_id columns for optimistic concurrency -------------------
    # server_default='1' ensures existing rows get a valid starting version
    # instead of NULL, so the column can be NOT NULL from the start.
    for table_name in ('section', 'sectionsynopsis', 'sectionnotes', 'sectioncharacters'):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(
                sa.Column('version_id', sa.Integer(), nullable=False, server_default='1')
            )


def downgrade():
    for table_name in ('section', 'sectionsynopsis', 'sectionnotes', 'sectioncharacters'):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column('version_id')

    op.drop_index('ix_checkpoint_section_checkpoint_id', table_name='checkpoint_section')
    op.drop_table('checkpoint_section')
    op.drop_table('checkpoint')
    # ### end Alembic commands ###
