from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR, UnicodeText
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    tsk = Table("task", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "task_assigned_user",
        meta,
        Column("id", Integer, primary_key=True),
        Column("task_id", Integer, ForeignKey(tsk.c.id), nullable=False, index=True),
        Column("user_id", Integer, ForeignKey(u.c.id), nullable=False, index=True),
        Column("notes", NVARCHAR(255)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    rs = Table("task_assigned_user", meta, autoload=True)
    rs.drop()
