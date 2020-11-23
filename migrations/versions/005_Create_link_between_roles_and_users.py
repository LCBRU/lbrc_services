from sqlalchemy import MetaData, Table, Index, Column, Integer

meta = MetaData()

roles_users = Table(
    "roles_users",
    meta,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer),
    Column("role_id", Integer),
)

Index("ix_roles_users_user_id", roles_users.c.user_id)
Index("ix_roles_users_role_id", roles_users.c.role_id)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    roles_users.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    roles_users.drop()
