"""Many to Many Tasks Organisations

Revision ID: d589c0923de6
Revises: 55b1004ec5e6
Create Date: 2023-09-29 08:23:44.325996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd589c0923de6'
down_revision = '55b1004ec5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tasks_organisations',
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.Column('organisation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['task.id'], )
    )


def downgrade() -> None:
    op.drop_table('tasks_organisations')
