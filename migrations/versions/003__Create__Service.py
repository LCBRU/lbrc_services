from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    fg = Table("field_group", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "service",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(200)),
        Column("field_group_id", Integer, ForeignKey(fg.c.id), index=True, nullable=False),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("service", meta, autoload=True)
    t.drop()
