from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    DateTime,
    NVARCHAR,
    Index,
    ForeignKey,
)


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    upload = Table("upload", meta, autoload=True)
    field = Table("field", meta, autoload=True)

    upload_data = Table(
        "upload_data",
        meta,
        Column("id", Integer, primary_key=True),
        Column(
            "upload_id", Integer, ForeignKey(upload.c.id), index=True, nullable=False
        ),
        Column("field_id", Integer, ForeignKey(field.c.id), index=True, nullable=False),
        Column("value", NVARCHAR(500)),
    )
    upload_data.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    upload_data = Table("upload_data", meta, autoload=True)
    upload_data.drop()
