from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    q = Table("quote", meta, autoload=True)

    t = Table(
        "quote_work_section",
        meta,
        Column("id", Integer, primary_key=True),
        Column("quote_id", Integer, ForeignKey(q.c.id), nullable=False, index=True),
        Column("name", NVARCHAR(255)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_work_section", meta, autoload=True)
    t.drop()
