from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    rt = Table("request_type", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "request",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(255)),
        Column("request_type_id", Integer, ForeignKey(rt.c.id), index=True, nullable=False),
        Column("requestor_id", Integer, ForeignKey(u.c.id), index=True, nullable=False),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("request", meta, autoload=True)
    t.drop()
