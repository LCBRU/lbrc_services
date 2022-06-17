from sqlalchemy import MetaData, Table, Column, UnicodeText


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("quote", meta, autoload=True)

    introduction = Column("introduction", UnicodeText)
    introduction.create(t)

    conclusion = Column("conclusion", UnicodeText)
    conclusion.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("quote", meta, autoload=True)
    t.c.introduction.drop()
    t.c.conclusion.drop()
