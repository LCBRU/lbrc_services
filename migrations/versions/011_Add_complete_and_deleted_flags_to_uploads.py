from sqlalchemy import MetaData, Table, Index, Column, Boolean

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    upload = Table("upload", meta, autoload=True)

    completed = Column("completed", Boolean)
    completed.create(upload)

    deleted = Column("deleted", Boolean)
    deleted.create(upload)

    idx_upload_completed = Index("idx_upload_completed", upload.c.completed)
    idx_upload_completed.create(migrate_engine)

    idx_upload_deleted = Index("idx_upload_deleted", upload.c.deleted)
    idx_upload_deleted.create(migrate_engine)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    upload = Table("upload", meta, autoload=True)

    idx_upload_completed = Index("idx_upload_completed", upload.c.completed)
    idx_upload_completed.drop(migrate_engine)

    idx_upload_deleted = Index("idx_upload_deleted", upload.c.deleted)
    idx_upload_deleted.drop(migrate_engine)

    upload.c.completed.drop()
    upload.c.deleted.drop()
