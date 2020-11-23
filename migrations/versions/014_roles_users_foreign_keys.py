from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, String
from migrate.changeset.constraint import ForeignKeyConstraint, UniqueConstraint


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    roles_users = Table("roles_users", meta, autoload=True)
    role = Table("role", meta, autoload=True)
    user = Table("user", meta, autoload=True)

    fk_role = ForeignKeyConstraint([roles_users.c.role_id], [role.c.id])
    fk_role.create()

    fk_user = ForeignKeyConstraint([roles_users.c.user_id], [user.c.id])
    fk_user.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    roles_users = Table("roles_users", meta, autoload=True)
    role = Table("role", meta, autoload=True)
    user = Table("user", meta, autoload=True)

    fk_role = ForeignKeyConstraint([roles_users.c.role_id], [role.c.id])
    fk_role.drop()

    fk_user = ForeignKeyConstraint([roles_users.c.user_id], [user.c.id])
    fk_user.drop()
