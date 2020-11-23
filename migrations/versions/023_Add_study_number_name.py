from sqlalchemy import MetaData, Table, Index, Column, Boolean, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("study", meta, autoload=True)

    study_number_name = Column("study_number_name", NVARCHAR(100))
    study_number_name.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("study", meta, autoload=True)

    study.c.study_number_name.drop()
