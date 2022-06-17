from sqlalchemy import ForeignKey, Integer, MetaData, Table, Column
from sqlalchemy import Index


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    pt = Table("quote_pricing_type", meta, autoload=True)

    t = Table("quote", meta, autoload=True)

    quote_pricing_type_id = Column("quote_pricing_type_id", Integer, ForeignKey(pt.c.id), nullable=True)
    quote_pricing_type_id.create(t)

    idx = Index('ix__quote__quote_pricing_type_id', t.c.quote_pricing_type_id)
    idx.create(migrate_engine)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.c.quote_pricing_type_id.drop()
