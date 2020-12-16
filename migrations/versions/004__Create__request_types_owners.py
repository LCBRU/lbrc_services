from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.sql.schema import ForeignKey

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    rt = Table("request_type", meta, autoload=True)
    u = Table("user", meta, autoload=True)

    t = Table(
        "request_types_owners",
        meta,
        Column("id", Integer, primary_key=True),
        Column("request_type_id", Integer, ForeignKey(rt.c.id), index=True, nullable=False),
        Column("user_id", Integer, ForeignKey(u.c.id), index=True, nullable=False),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("request_types_owners", meta, autoload=True)
    t.drop()
