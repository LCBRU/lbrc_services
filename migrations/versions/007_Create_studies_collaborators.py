from sqlalchemy import MetaData, Table, Index, Column, Integer

meta = MetaData()

studies_collaborators = Table(
    "studies_collaborators",
    meta,
    Column("id", Integer, primary_key=True),
    Column("study_id", Integer),
    Column("user_id", Integer),
)

Index("ix_studies_collaborators_study_id", studies_collaborators.c.study_id)
Index("ix_studies_collaborators_user_id", studies_collaborators.c.user_id)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    studies_collaborators.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    studies_collaborators.drop()
