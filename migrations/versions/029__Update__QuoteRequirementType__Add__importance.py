from sqlalchemy import Integer, MetaData, Table, Column, UnicodeText


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote_requirement_type", meta, autoload=True)

    importance = Column("importance", Integer, default=0)
    importance.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_requirement_type", meta, autoload=True)
    t.c.importance.drop()
