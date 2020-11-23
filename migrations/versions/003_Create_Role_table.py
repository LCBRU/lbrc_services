from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR

meta = MetaData()

role = Table(
    "role",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(100)),
    Column("description", NVARCHAR(250)),
    Column("date_created", DateTime),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    role.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    role.drop()
