#!/usr/bin/env python3

from dotenv import load_dotenv
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users, add_user_to_role
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from random import randint, choice, sample
from lbrc_services.model.quotes import Quote, QuotePricingType, QuoteRequirement, QuoteRequirementType, QuoteStatus, QuoteStatusType, QuoteWorkLine, QuoteWorkSection
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

for r in get_roles():
    add_user_to_role(user=me, role_name=r)

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
    Service(name=fg.name, field_group=fg, description='\n\n'.join(fake.paragraphs(nb=randint(1,5))), owners=[me])
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

quote_status_types = list(db.session.execute(select(QuoteStatusType)).scalars())
quote_pricing_types = list(db.session.execute(select(QuotePricingType)).scalars())

quotes = []
for o in organisations:
    for _ in range(randint(5,10)):
        quotes.append(
            Quote(
                name=fake.sentence(),
                organisation=o,
                requestor=choice(other_users),
                current_status_type=choice(quote_status_types),
                introduction=fake.paragraph(nb_sentences=randint(2, 5)),
                conclusion=fake.paragraph(nb_sentences=randint(2, 5)),
                quote_pricing_type=choice(quote_pricing_types),
                date_requested=fake.date(),
                date_required=fake.date(),
                reference=fake.sentence(),
            )
        )
db.session.add_all(quotes)
db.session.commit()

quote_statuses = []
for qws in quotes:
    for _ in range(randint(2,10)):
        quote_statuses.append(
            QuoteStatus(
                quote=qws,
                notes=fake.paragraph(nb_sentences=randint(1, 3)),
                quote_status_type=choice(quote_status_types),
            )
        )
    quote_statuses.append(
        QuoteStatus(
            quote=qws,
            notes=fake.paragraph(nb_sentences=randint(1, 3)),
            quote_status_type=qws.current_status_type,
        )
    )
db.session.add_all(quote_statuses)
db.session.commit()


quote_requirement_types = list(db.session.execute(select(QuoteRequirementType)).scalars())

quote_requirements = []
for qws in quotes:
    for _ in range(randint(2,10)):
        quote_requirements.append(
            QuoteRequirement(
                quote=qws,
                notes=fake.paragraph(nb_sentences=randint(1, 3)),
                quote_requirement_type=choice(quote_requirement_types),
            )
        )
db.session.add_all(quote_requirements)
db.session.commit()

quote_work_sections = []
for qws in quotes:
    for _ in range(randint(2,10)):
        quote_work_sections.append(
            QuoteWorkSection(
                quote=qws,
                name=fake.sentence(nb_words=randint(1,10)),
            )
        )
db.session.add_all(quote_work_sections)
db.session.commit()

quote_work_line = []
for qws in quote_work_sections:
    for _ in range(randint(2,10)):
        quote_work_line.append(
            QuoteWorkLine(
                quote_work_section=qws,
                name=fake.sentence(nb_words=randint(1,10)),
                days=randint(1,20) * 0.5,
            )
        )
db.session.add_all(quote_work_line)
db.session.commit()

db.session.close()
