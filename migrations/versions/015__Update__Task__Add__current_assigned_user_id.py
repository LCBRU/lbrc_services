from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import Index


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    u = Table("user", meta, autoload=True)
    t = Table("task", meta, autoload=True)

    current_assigned_user_id = Column("current_assigned_user_id", Integer, ForeignKey(u.c.id), nullable=True)
    current_assigned_user_id.create(t)

    idx = Index('ix__task__current_assigned_user_id', t.c.current_assigned_user_id)
    idx.create(migrate_engine)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("task", meta, autoload=True)
    t.c.current_assigned_user_id.drop()
