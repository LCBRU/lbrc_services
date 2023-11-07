#!/usr/bin/env python3

from dotenv import load_dotenv
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from lbrc_services.model.security import get_roles
from lbrc_services.model import task_status_type_setup
from lbrc_services.model import services
from lbrc_flask.forms.dynamic import FieldGroup, create_field_types, FieldType


load_dotenv()

from lbrc_services import create_app

application = create_app()
application.app_context().push()
db.create_all()

alembic_cfg = Config("alembic.ini")
command.stamp(alembic_cfg, "head")

init_roles(get_roles())
init_users()

task_status_type_setup()
create_field_types()

me = db.session.execute(
    select(services.User).filter(services.User.username == 'rab')
).scalar()

for fg in ['Group A', 'Group B']:
    db.session.add(services.FieldGroup(name=fg))
db.session.commit()

for f in [
    {
        'group_name': 'Group A',
        'order': 1,
        'type': FieldType.STRING,
        'field_name': 'Hello',
    },
    {
        'group_name': 'Group A',
        'order': 2,
        'type': FieldType.STRING,
        'field_name': 'Goodbye',
    },
    {
        'group_name': 'Group B',
        'order': 1,
        'type': FieldType.STRING,
        'field_name': 'Ciao',
    },
    ]:
    db.session.add(services.Field(
        field_name=f['field_name'],
        order=f['order'],
        field_type=FieldType._get_field_type(f['type']),
        field_group=db.session.execute(select(FieldGroup).filter(FieldGroup.name == f['group_name'])).scalar(),
    ))
db.session.commit()


for s in [
    {'name': 'Service A', 'group_name': 'Group A'},
    {'name': 'Service B', 'group_name': 'Group B'},
]:
    db.session.add(services.Service(
        name=s['name'],
        field_group=db.session.execute(select(FieldGroup).filter(FieldGroup.name == s['group_name'])).scalar(), 
    ))

    serv = db.session.execute(
        select(services.Service)
        .filter(services.Service.name == s['name'])
    ).scalar()

    serv.owners = [me]
    db.session.add(serv)

db.session.commit()

db.session.close()
