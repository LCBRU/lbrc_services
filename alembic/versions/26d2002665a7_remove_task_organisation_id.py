"""Remove Task Organisation ID

Revision ID: 26d2002665a7
Revises: d589c0923de6
Create Date: 2023-09-29 13:58:41.826595

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '26d2002665a7'
down_revision = 'd589c0923de6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_constraint('task_ibfk_1', type_='foreignkey')
        batch_op.drop_column('organisation_id')


def downgrade() -> None:
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organisation_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('task_ibfk_1', 'organisation', ['organisation_id'], ['id'])
