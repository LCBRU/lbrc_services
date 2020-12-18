from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR, BOOLEAN

meta = MetaData()


t = Table(
    "request_status",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(255)),
    Column("is_complete", BOOLEAN),
    Column("is_active", BOOLEAN),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("request_status", meta, autoload=True)
    t.drop()
