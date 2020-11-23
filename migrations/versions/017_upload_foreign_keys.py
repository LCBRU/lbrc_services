from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, String
from migrate.changeset.constraint import ForeignKeyConstraint, UniqueConstraint


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    upload = Table("upload", meta, autoload=True)
    study = Table("study", meta, autoload=True)
    user = Table("user", meta, autoload=True)

    fk_study = ForeignKeyConstraint([upload.c.study_id], [study.c.id])
    fk_study.create()

    fk_user = ForeignKeyConstraint([upload.c.uploader_id], [user.c.id])
    fk_user.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    upload = Table("upload", meta, autoload=True)
    study = Table("study", meta, autoload=True)
    user = Table("user", meta, autoload=True)

    fk_study = ForeignKeyConstraint([upload.c.study_id], [study.c.id])
    fk_study.drop()

    fk_user = ForeignKeyConstraint([upload.c.uploader_id], [user.c.id])
    fk_user.drop()
