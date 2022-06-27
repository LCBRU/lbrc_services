from sqlalchemy import MetaData, Table, Column, UnicodeText


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote_requirement_type", meta, autoload=True)

    description = Column("description", UnicodeText)
    description.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote_requirement_type", meta, autoload=True)
    t.c.description.drop()
