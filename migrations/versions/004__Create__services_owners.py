from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.sql.schema import ForeignKey

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    s = Table("service", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "services_owners",
        meta,
        Column("id", Integer, primary_key=True),
        Column("service_id", Integer, ForeignKey(s.c.id), index=True, nullable=False),
        Column("user_id", Integer, ForeignKey(u.c.id), index=True, nullable=False),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("services_owners", meta, autoload=True)
    t.drop()
