from sqlalchemy import MetaData, Table, Column, Integer, DateTime, NVARCHAR, Boolean

meta = MetaData()

user = Table(
    "user",
    meta,
    Column("id", Integer, primary_key=True),
    Column("email", NVARCHAR(255), unique=True),
    Column("password", NVARCHAR(255)),
    Column("first_name", NVARCHAR(255)),
    Column("last_name", NVARCHAR(255)),
    Column("active", Boolean()),
    Column("confirmed_at", DateTime()),
    Column("last_login_at", DateTime()),
    Column("current_login_at", DateTime()),
    Column("last_login_ip", NVARCHAR(50)),
    Column("current_login_ip", NVARCHAR(50)),
    Column("login_count", Integer),
    Column("date_created", DateTime),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    user.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    user.drop()
