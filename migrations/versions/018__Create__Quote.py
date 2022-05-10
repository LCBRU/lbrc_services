from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    o = Table("organisation", meta, autoload=True)
    qst = Table("quote_status_type", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "quote",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(255)),
        Column("organisation_id", Integer, ForeignKey(o.c.id), index=True, nullable=False),
        Column("organisation_description", NVARCHAR(255)),
        Column("requestor_id", Integer, ForeignKey(u.c.id), index=True, nullable=False),
        Column("current_status_type_id", Integer, ForeignKey(qst.c.id), nullable=False, index=True),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.drop()
