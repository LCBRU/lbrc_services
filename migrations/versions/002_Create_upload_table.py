from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, Boolean

meta = MetaData()

upload = Table(
    "upload",
    meta,
    Column("id", Integer, primary_key=True),
    Column("study_id", Integer),
    Column("study_number", NVARCHAR(20), unique=True),
    Column("date_created", DateTime),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    upload.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    upload.drop()
