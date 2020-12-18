from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    r = Table("request", meta, autoload=True)
    rst = Table("request_status_type", meta, autoload=True)

    rs = Table(
        "request_status",
        meta,
        Column("id", Integer, primary_key=True),
        Column("request_id", Integer, ForeignKey(r.c.id), nullable=False, index=True),
        Column("notes", NVARCHAR(255)),
        Column("request_status_type_id", Integer, ForeignKey(rst.c.id), nullable=False, index=True),
        *get_audit_mixin_columns(),
    )

    rs.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    rs = Table("request_status", meta, autoload=True)
    rs.drop()
