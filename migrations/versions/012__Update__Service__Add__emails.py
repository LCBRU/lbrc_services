from sqlalchemy import MetaData, Table, Column, Boolean, NVARCHAR
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    s = Table("service", meta, autoload=True)

    generic_recipients = Column("generic_recipients", NVARCHAR(255))
    generic_recipients.create(s)

    suppress_owner_email = Column("suppress_owner_email", Boolean, default=False)
    suppress_owner_email.create(s)

    s.c.suppress_owner_email.alter(nullable=False)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    s = Table("service", meta, autoload=True)
    s.c.generic_recipients.drop()
    s.c.suppress_owner_email.drop()