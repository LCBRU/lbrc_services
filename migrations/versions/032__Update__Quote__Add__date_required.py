from sqlalchemy import MetaData, Table, Column, DATE


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote", meta, autoload=True)

    reference = Column("date_required", DATE)
    reference.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.c.date_required.drop()
