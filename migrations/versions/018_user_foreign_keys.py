from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    DateTime,
    NVARCHAR,
    String,
    ForeignKey,
)
from migrate.changeset.constraint import ForeignKeyConstraint


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    user = Table("user", meta, autoload=True)
    site = Table("site", meta, autoload=True)

    fk_site = ForeignKeyConstraint([user.c.site_id], [site.c.id])
    fk_site.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    user = Table("user", meta, autoload=True)
    site = Table("site", meta, autoload=True)

    fk_site = ForeignKeyConstraint([user.c.site_id], [site.c.id])
    fk_site.drop()
