from sqlalchemy import MetaData, Table, Index, Column, Integer

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    upload = Table("upload", meta, autoload=True)

    uploader_id = Column("uploader_id", Integer)
    uploader_id.create(upload)

    idx_upload_uploader_id = Index("idx_upload_uploader_id", upload.c.uploader_id)
    idx_upload_uploader_id.create(migrate_engine)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    upload = Table("upload", meta, autoload=True)

    idx_upload_uploader_id = Index("idx_upload_uploader_id", upload.c.uploader_id)
    idx_upload_uploader_id.drop(migrate_engine)

    upload.c.uploader_id.drop()
