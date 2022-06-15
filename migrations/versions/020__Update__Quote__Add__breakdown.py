from sqlalchemy import MetaData, Table, Column, Integer, UnicodeText
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import Index
from sqlalchemy.sql.sqltypes import Boolean


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote", meta, autoload=True)

    number_of_sites = Column("number_of_sites", Integer)
    number_of_sites.create(t)
    length_of_study_months = Column("length_of_study_months", Integer)
    length_of_study_months.create(t)
    number_of_participants = Column("number_of_participants", Integer)
    number_of_participants.create(t)
    number_of_crfs = Column("number_of_crfs", Integer)
    number_of_crfs.create(t)
    number_of_visits = Column("number_of_visits", Integer)
    number_of_visits.create(t)
    other_requirements = Column("other_requirements", UnicodeText)
    other_requirements.create(t)
    out_of_scope = Column("out_of_scope", UnicodeText)
    out_of_scope.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.c.number_of_sites.drop()
    t.c.length_of_study_months.drop()
    t.c.number_of_participants.drop()
    t.c.number_of_crfs.drop()
    t.c.number_of_visits.drop()
    t.c.other_requirements.drop()
    t.c.out_of_scope.drop()
