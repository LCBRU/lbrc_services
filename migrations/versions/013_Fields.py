from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    DateTime,
    NVARCHAR,
    String,
    Index,
    Boolean,
)
from migrate.changeset.constraint import ForeignKeyConstraint, UniqueConstraint


meta = MetaData()

field = Table(
    "field",
    meta,
    Column("id", Integer, primary_key=True),
    Column("study_id", Integer),
    Column("order", Integer),
    Column("field_type_id", Integer),
    Column("field_name", String(100)),
    Column("required", Boolean),
    Column("max_length", Integer),
    Column("default", String(250)),
    Column("choices", String(250)),
    Column("allowed_file_extensions", String(250)),
)

Index("ix_field_study_id", field.c.study_id)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    field.create()

    field_type = Table("field_type", meta, autoload=True)
    study = Table("study", meta, autoload=True)

    fk_field_type = ForeignKeyConstraint([field.c.field_type_id], [field_type.c.id])
    fk_field_type.create()

    fk_study = ForeignKeyConstraint([field.c.study_id], [study.c.id])
    fk_study.create()

    uk_study_id_order = UniqueConstraint(field.c.study_id, field.c.order, table=field)
    uk_study_id_order.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    field.drop()
