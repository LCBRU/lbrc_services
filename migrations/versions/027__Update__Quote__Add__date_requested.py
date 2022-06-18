from sqlalchemy import MetaData, Table, Column, Date


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote", meta, autoload=True)

    date_requested = Column("date_requested", Date)
    date_requested.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.c.date_requested.drop()
