from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR, BOOLEAN
from sqlalchemy.sql import Select
from lbrc_requests.model import RequestStatus


meta = MetaData()

statuses = {
    RequestStatus.CREATED: {
        'is_complete': False,
        'is_active': False,
    },
    RequestStatus.IN_PROGRESS: {
        'is_complete': False,
        'is_active': True,
    },
    RequestStatus.COMPLETE: {
        'is_complete': True,
        'is_active': False,
    },
    RequestStatus.AWAITING_INFORMATION: {
        'is_complete': False,
        'is_active': False,
    },
    RequestStatus.CANCELLED: {
        'is_complete': True,
        'is_active': False,
    },
}


request_status = Table(
    "request_status",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(255)),
    Column("is_complete", BOOLEAN),
    Column("is_active", BOOLEAN),
)


def upgrade(migrate_engine):
    conn = migrate_engine.connect()

    for name, status in statuses.items():
        conn.execute(request_status.insert().values(
            name=name,
            is_complete=status['is_complete'],
            is_active=status['is_active'],
        ))


def downgrade(migrate_engine):
    conn = migrate_engine.connect()

    conn.execute(request_status.delete())
