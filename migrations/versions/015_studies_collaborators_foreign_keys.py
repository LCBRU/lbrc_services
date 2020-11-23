from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, String
from migrate.changeset.constraint import ForeignKeyConstraint, UniqueConstraint


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    studies_collaborators = Table("studies_collaborators", meta, autoload=True)
    study = Table("study", meta, autoload=True)
    user = Table("user", meta, autoload=True)

    fk_study = ForeignKeyConstraint([studies_collaborators.c.study_id], [study.c.id])
    fk_study.create()

    fk_user = ForeignKeyConstraint([studies_collaborators.c.user_id], [user.c.id])
    fk_user.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    studies_collaborators = Table("studies_collaborators", meta, autoload=True)
    study = Table("study", meta, autoload=True)
    user = Table("user", meta, autoload=True)

    fk_study = ForeignKeyConstraint([studies_collaborators.c.study_id], [study.c.id])
    fk_study.drop()

    fk_user = ForeignKeyConstraint([studies_collaborators.c.user_id], [user.c.id])
    fk_user.drop()
