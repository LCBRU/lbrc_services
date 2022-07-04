from sqlalchemy import NVARCHAR, MetaData, Table, Column


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote", meta, autoload=True)

    reference = Column("reference", NVARCHAR(100))
    reference.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.c.reference.drop()
