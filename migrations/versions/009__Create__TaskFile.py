from sqlalchemy import MetaData, Table, Column, Integer, DateTime, UnicodeText, NVARCHAR
from sqlalchemy.sql.schema import ForeignKey
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    f = Table("field", meta, autoload=True)
    tsk = Table("task", meta, autoload=True)

    t = Table(
        "task_file",
        meta,
        Column("id", Integer, primary_key=True),
        Column("filename", UnicodeText),
        Column("local_filepath", UnicodeText),
        Column("task_id", Integer, ForeignKey(tsk.c.id), index=True, nullable=False),
        Column("field_id", Integer, ForeignKey(f.c.id), index=True, nullable=False),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("task_file", meta, autoload=True)
    t.drop()
