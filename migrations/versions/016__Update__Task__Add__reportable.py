from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import Index
from sqlalchemy.sql.sqltypes import Boolean


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("field", meta, autoload=True)

    reportable = Column("reportable", Boolean)
    reportable.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("field", meta, autoload=True)
    t.c.reportable.drop()
