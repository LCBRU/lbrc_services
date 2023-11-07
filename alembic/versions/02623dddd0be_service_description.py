"""Service description

Revision ID: 02623dddd0be
Revises: 26d2002665a7
Create Date: 2023-09-29 14:53:18.792815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02623dddd0be'
down_revision = '26d2002665a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.UnicodeText(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_column('description')
