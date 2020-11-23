from sqlalchemy import MetaData, Table, Index, Column, Boolean, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("study", meta, autoload=True)

    study_number_format = Column("study_number_format", NVARCHAR(50))
    study_number_format.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("study", meta, autoload=True)

    study.c.study_number_format.drop()
