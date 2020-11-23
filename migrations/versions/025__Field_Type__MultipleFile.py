from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, Boolean
from sqlalchemy.orm import sessionmaker
from lbrc_requests.model import FieldType


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    session.add(FieldType(name="MultipleFileField", is_file=True))

    session.commit()


def downgrade(migrate_engine):
    pass
