from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR, Index, ForeignKey


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    field = Table("field", meta, autoload=True)
    upload = Table("upload", meta, autoload=True)

    upload_file = Table(
        "upload_file",
        meta,
        Column("id", Integer, primary_key=True),
        Column(
            "upload_id", Integer, ForeignKey(upload.c.id), index=True, nullable=False
        ),
        Column("field_id", Integer, ForeignKey(field.c.id), index=True, nullable=False),
        Column("filename", NVARCHAR(500), nullable=False),
    )
    upload_file.create()


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    upload_file = Table("upload_file", meta, autoload=True)
    upload_file.drop()
