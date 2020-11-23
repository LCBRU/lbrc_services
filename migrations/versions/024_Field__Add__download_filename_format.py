from sqlalchemy import MetaData, Table, Index, Column, Boolean, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    download_filename_format = Column("download_filename_format", NVARCHAR(200))
    download_filename_format.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    study.c.download_filename_format.drop()
