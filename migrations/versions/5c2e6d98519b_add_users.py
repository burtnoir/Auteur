"""Add Users

Revision ID: 5c2e6d98519b
Revises: 86314a8f0dc1
Create Date: 2026-08-09 15:25:34.682796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c2e6d98519b'
down_revision = '86314a8f0dc1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=1000), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    # Create a default user so existing projects have someone to belong to.
    # NOTE: replace the placeholder password with a properly hashed value
    # before running this against a real database.
    users_table = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('email', sa.String),
        sa.column('password', sa.String),
        sa.column('name', sa.String),
    )
    op.bulk_insert(users_table, [
        {
            'id': 1,
            'email': 'default@example.com',
            'password': 'pbkdf2:sha256:1000000$BJfhU6Ih$05829784cd00ba03c2ac31234ab01f30c27fc8686150ab4a888285147fb1f56e',
            'name': 'Default User',
        }
    ])

    # Add user_id as nullable first, backfill it, then tighten to NOT NULL.
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))

    op.execute('UPDATE project SET user_id = 1 WHERE user_id IS NULL')

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.create_foreign_key('fx_project_users', 'users', ['user_id'], ['id'])


def downgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_constraint('fx_project_users', type_='foreignkey')
        batch_op.drop_column('user_id')

    op.drop_table('users')