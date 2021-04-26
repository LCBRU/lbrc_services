from sqlalchemy import MetaData, Table, Column, UnicodeText
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    s = Table("service", meta, autoload=True)

    instroduction = Column("introduction", UnicodeText)
    instroduction.create(s)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    s = Table("service", meta, autoload=True)
    s.c.instroduction.drop()
