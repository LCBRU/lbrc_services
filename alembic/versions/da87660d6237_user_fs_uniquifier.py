"""User fs_uniquifier

Revision ID: da87660d6237
Revises: 
Create Date: 2023-05-22 15:55:39.969500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da87660d6237'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('user', 'fs_uniquifier')
    op.add_column('user', sa.Column('fs_uniquifier', sa.String(255), nullable=True))
    op.create_unique_constraint("uq_user_fs_uniquifier", "user", ["fs_uniquifier"])

def downgrade() -> None:
    op.drop_column('user', 'fs_uniquifier')
