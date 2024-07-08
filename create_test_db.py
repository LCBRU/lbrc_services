#!/usr/bin/env python3

from dotenv import load_dotenv
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from random import randint, choice, sample
from lbrc_services.model.security import get_roles
from lbrc_services.model import task_status_type_setup
from lbrc_services.model.services import Organisation, Task, TaskStatusType, User, Service
from lbrc_flask.forms.dynamic import FieldGroup, create_field_types, FieldType, Field
from faker import Faker
fake = Faker()


load_dotenv()

def unique_words():
    return {fake.word().title() for _ in range(randint(20, 40))}


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
    select(User).filter(User.id == 2)
).scalar()

other_users = [User(
    email=fake.email(),
    username=''.join(fake.random_letters())
) for _ in range(randint(10, 20))]
db.session.add_all(other_users)
db.session.commit()

field_groups = [
    FieldGroup(name=s)
    for s in unique_words()
]
db.session.add_all(field_groups)
db.session.commit()

services = [
    Service(name=fg.name, field_group=fg, owners=[me])
    for fg in field_groups
]
db.session.add_all(services)
db.session.commit()

field_types = FieldType.all_field_types()

fields = []
for fg in field_groups:
    for i in range(1, randint(10, 20)):
        fields.append(
            Field(
                field_name=fake.sentence().title(),
                order=i,
                field_type=choice(field_types),
                field_group=fg,
            )
        )
db.session.add_all(fields)
db.session.commit()

task_statuses = TaskStatusType.get_all_task_statuses()
organisations = Organisation.get_all_organisations()

tasks = []
for s in services:
    for _ in range(randint(5,10)):
        tasks.append(
            Task(
                name=fake.sentence(),
                service=s,
                requestor=choice(other_users),
                current_status_type=choice(task_statuses),
                current_assigned_user=me,
                organisations=sample(organisations, randint(1, 3)),
            )
        )
db.session.add_all(tasks)
db.session.commit()

db.session.close()
