from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR, DECIMAL
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    ws = Table("quote_work_section", meta, autoload=True)

    t = Table(
        "quote_work_line",
        meta,
        Column("id", Integer, primary_key=True),
        Column("quote_work_section_id", Integer, ForeignKey(ws.c.id), nullable=False, index=True),
        Column("name", NVARCHAR(255)),
        Column("days", DECIMAL(10,2)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_work_line", meta, autoload=True)
    t.drop()
