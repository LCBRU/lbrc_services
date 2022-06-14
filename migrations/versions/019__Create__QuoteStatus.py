from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    q = Table("quote", meta, autoload=True)
    qst = Table("quote_status_type", meta, autoload=True)

    qs = Table(
        "quote_status",
        meta,
        Column("id", Integer, primary_key=True),
        Column("quote_id", Integer, ForeignKey(q.c.id), nullable=False, index=True),
        Column("notes", NVARCHAR(255)),
        Column("quote_status_type_id", Integer, ForeignKey(qst.c.id), nullable=False, index=True),
        *get_audit_mixin_columns(),
    )

    qs.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    qs = Table("quote_status", meta, autoload=True)
    qs.drop()
