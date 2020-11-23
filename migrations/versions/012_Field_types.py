from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, Boolean
from sqlalchemy.orm import sessionmaker
from lbrc_requests.model import FieldType


meta = MetaData()

field_type = Table(
    "field_type",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(255), unique=True),
    Column("is_file", Boolean),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    field_type.create()

    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    for t in [
        "BooleanField",
        "IntegerField",
        "RadioField",
        "StringField",
        "TextAreaField",
    ]:
        ft = FieldType(name=t)
        session.add(ft)

    session.add(FieldType(name="FileField", is_file=True))

    session.commit()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    field_type.drop()
