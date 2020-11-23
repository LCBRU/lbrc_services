from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR

meta = MetaData()

site = Table(
    "site",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(255), unique=True),
    Column("number", NVARCHAR(255), unique=True),
    Column("date_created", DateTime),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    site.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    site.drop()
