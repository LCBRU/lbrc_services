from sqlalchemy import MetaData, Table, Column, Integer, UnicodeText
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    r = Table("request", meta, autoload=True)

    rs = Table(
        "to_do",
        meta,
        Column("id", Integer, primary_key=True),
        Column("request_id", Integer, ForeignKey(r.c.id), nullable=False, index=True),
        Column("description", UnicodeText),
        Column("status", Integer, CheckConstraint("status IN (-1, 0, 1)")),
        *get_audit_mixin_columns(),
    )

    rs.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    rs = Table("to_do", meta, autoload=True)
    rs.drop()
