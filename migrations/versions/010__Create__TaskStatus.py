from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    tsk = Table("task", meta, autoload=True)
    tst = Table("task_status_type", meta, autoload=True)

    ts = Table(
        "task_status",
        meta,
        Column("id", Integer, primary_key=True),
        Column("task_id", Integer, ForeignKey(tsk.c.id), nullable=False, index=True),
        Column("notes", NVARCHAR(255)),
        Column("task_status_type_id", Integer, ForeignKey(tst.c.id), nullable=False, index=True),
        *get_audit_mixin_columns(),
    )

    ts.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    rs = Table("tst_status", meta, autoload=True)
    rs.drop()
