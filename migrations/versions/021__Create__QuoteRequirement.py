from sqlalchemy import MetaData, Table, Column, Integer, UnicodeText
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    q = Table("quote", meta, autoload=True)
    qrt = Table("quote_requirement_type", meta, autoload=True)

    qr = Table(
        "quote_requirement",
        meta,
        Column("id", Integer, primary_key=True),
        Column("quote_id", Integer, ForeignKey(q.c.id), nullable=False, index=True),
        Column("notes", UnicodeText),
        Column("quote_requirement_type_id", Integer, ForeignKey(qrt.c.id), nullable=False, index=True),
        *get_audit_mixin_columns(),
    )

    qr.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_requirement", meta, autoload=True)
    t.drop()
