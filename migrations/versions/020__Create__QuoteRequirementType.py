from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    qs = Table(
        "quote_requirement_type",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(255)),
    )

    qs.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    qs = Table("quote_requirement_type", meta, autoload=True)
    qs.drop()
