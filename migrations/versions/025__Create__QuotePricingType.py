from sqlalchemy import BOOLEAN, MetaData, Table, Column, Integer, NVARCHAR, DECIMAL
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table(
        "quote_pricing_type",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(255)),
        Column("price_per_day", DECIMAL()),
        Column("disabled", BOOLEAN()),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_pricing_type", meta, autoload=True)
    t.drop()
