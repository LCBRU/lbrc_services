from sqlalchemy import MetaData, Table, Column, Integer, UnicodeText, Boolean
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table(
        "quote_status_type",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", UnicodeText),
        Column("is_complete", Boolean,),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_status_type", meta, autoload=True)
    t.drop()
