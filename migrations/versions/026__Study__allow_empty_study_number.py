from sqlalchemy import MetaData, Table, Index, Column, Boolean

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("study", meta, autoload=True)

    allow_empty_study_number = Column("allow_empty_study_number", Boolean, default=False)
    allow_empty_study_number.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("study", meta, autoload=True)

    study.c.allow_empty_study_number.drop()
