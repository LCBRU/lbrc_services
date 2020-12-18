from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR, BOOLEAN
from lbrc_requests.model import RequestStatusType


meta = MetaData()

statuses = {
    RequestStatusType.CREATED: {
        'is_complete': False,
        'is_active': False,
    },
    RequestStatusType.IN_PROGRESS: {
        'is_complete': False,
        'is_active': True,
    },
    RequestStatusType.COMPLETE: {
        'is_complete': True,
        'is_active': False,
    },
    RequestStatusType.AWAITING_INFORMATION: {
        'is_complete': False,
        'is_active': False,
    },
    RequestStatusType.CANCELLED: {
        'is_complete': True,
        'is_active': False,
    },
}


request_status_type = Table(
    "request_status_type",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", NVARCHAR(255)),
    Column("is_complete", BOOLEAN),
    Column("is_active", BOOLEAN),
)


def upgrade(migrate_engine):
    conn = migrate_engine.connect()

    for name, status in statuses.items():
        conn.execute(request_status_type.insert().values(
            name=name,
            is_complete=status['is_complete'],
            is_active=status['is_active'],
        ))


def downgrade(migrate_engine):
    conn = migrate_engine.connect()

    conn.execute(request_status_type.delete())
