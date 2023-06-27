"""Do not show field

Revision ID: 55b1004ec5e6
Revises: da87660d6237
Create Date: 2023-06-27 14:47:27.776647

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '55b1004ec5e6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
        'field',  
        sa.Column('do_not_show', sa.Boolean(), nullable=True)  
	)
	op.execute("UPDATE field SET do_not_show = false")
	op.alter_column('field', 'do_not_show', existing_type=sa.Boolean(), nullable=False)


def downgrade() -> None:
    op.drop_column('field', 'do_not_show')
