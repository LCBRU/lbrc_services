from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    tst = Table("task_status_type", meta, autoload=True)
    s = Table("service", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "task",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(255)),
        Column("service_id", Integer, ForeignKey(s.c.id), index=True, nullable=False),
        Column("requestor_id", Integer, ForeignKey(u.c.id), index=True, nullable=False),
        Column("current_status_type_id", Integer, ForeignKey(tst.c.id), nullable=False, index=True),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("task", meta, autoload=True)
    t.drop()
