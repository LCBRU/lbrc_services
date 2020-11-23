from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR

meta = MetaData()

study = Table(
    "study",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(200)),
    Column("date_created", DateTime),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    study.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    study.drop()
