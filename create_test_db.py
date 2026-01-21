#!/usr/bin/env python3

from dotenv import load_dotenv

load_dotenv()

from itertools import product
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users, add_user_to_role
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from random import randint, choice, sample
from lbrc_services.model.security import get_roles
from lbrc_services.model import task_status_type_setup
from lbrc_services.model.services import Organisation, TaskStatusType, User
from lbrc_flask.forms.dynamic import create_field_types
from faker import Faker
from lbrc_flask.pytest.faker import FieldsProvider
from tests.faker import LbrcServicesProvider


fake = Faker("en_GB")
fake.add_provider(FieldsProvider)
fake.add_provider(LbrcServicesProvider)

from lbrc_services import create_app


def create_quotes(fake):
    organisations = Organisation.get_all_organisations()

    quotes = []
    for o in organisations:
        quotes.extend(fake.quote().get_list(save=True, organisation=o, item_count=randint(5,10)))

    for qws in quotes:
        fake.quote_status().get_list(save=True, quote=qws, item_count=randint(2,10))
        fake.quote_status().get(save=True, quote=qws, quote_status_type=qws.current_status_type)

    for qws in quotes:
        fake.quote_requirement().get_list(save=True, quote=qws, item_count=randint(2,10))

    quote_work_sections = []
    for qws in quotes:
        quote_work_sections.extend(fake.quote_work_section().get_list(save=True, quote=qws, item_count=randint(2,10)))

    for qws in quote_work_sections:
        fake.quote_work_line().get_list(save=True, quote_work_section=qws, item_count=randint(2,10))


def create_services_and_tasks(fake, admin_user, quoters, other_users):
    organisations = Organisation.get_all_organisations()

    services = []
    for _ in range(randint(5, 10)):
        services.append(fake.service().get(save=True, owners=sample(quoters, randint(1, 2)) + [admin_user]))

    for fg in [s.field_group for s in services]:
        fake.field().get_list(save=True, field_group=fg, item_count=randint(5, 10))

    task_statuses = TaskStatusType.get_all_task_statuses()

    for s in services:
        for _ in range(randint(5,10)):
            fake.task().get(save=True, 
                service=s,
                requestor=choice(other_users),
                current_status_type=choice(task_statuses),
                current_assigned_user=choice(quoters),
                organisations=sample(organisations, randint(1, 3)),
            )


application = create_app()
application.app_context().push()
db.create_all()

alembic_cfg = Config("alembic.ini")
command.stamp(alembic_cfg, "head")

init_roles(get_roles())
init_users()

task_status_type_setup()
create_field_types()

admin_user = db.session.execute(select(User).filter(User.id == 2)).scalar()

quoters = [admin_user] + fake.user().get_list(save=True, item_count=randint(5, 10))
other_users = fake.user().get_list(save=True, item_count=randint(10, 20))

for r, u in product(get_roles(), quoters):
    add_user_to_role(user=u, role_name=r)

create_services_and_tasks(fake, admin_user, quoters, other_users)
create_quotes(fake)

db.session.close()
