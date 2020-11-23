from sqlalchemy import MetaData, Table, Index, Column, Integer

meta = MetaData()

studies_owners = Table(
    "studies_owners",
    meta,
    Column("id", Integer, primary_key=True),
    Column("study_id", Integer),
    Column("user_id", Integer),
)

Index("ix_studies_owners_study_id", studies_owners.c.study_id)
Index("ix_studies_owners_user_id", studies_owners.c.user_id)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    studies_owners.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    studies_owners.drop()
