from sqlalchemy import MetaData, Table, Column, Integer, DateTime, UnicodeText, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    f = Table("field", meta, autoload=True)
    r = Table("request", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "request_data",
        meta,
        Column("id", Integer, primary_key=True),
        Column("value", UnicodeText),
        Column("request_id", Integer, ForeignKey(r.c.id), index=True, nullable=False),
        Column("field_id", Integer, ForeignKey(f.c.id), index=True, nullable=False),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("request_data", meta, autoload=True)
    t.drop()
