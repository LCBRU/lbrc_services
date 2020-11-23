from sqlalchemy import MetaData, Table, Index, Column, Integer

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    user = Table("user", meta, autoload=True)

    site_id = Column("site_id", Integer)
    site_id.create(user)

    idx_user_site_id = Index("idx_user_sire_id", user.c.site_id)
    idx_user_site_id.create(migrate_engine)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    user = Table("user", meta, autoload=True)

    idx_user_site_id = Index("idx_user_sire_id", user.c.site_id)
    idx_user_site_id.drop(migrate_engine)

    user.c.site_id.drop()
