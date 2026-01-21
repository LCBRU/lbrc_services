from datetime import datetime
from functools import cache
from random import choice, randint
from typing import Optional
from faker.providers import BaseProvider
from lbrc_services.model.quotes import Quote, QuotePricingType, QuoteRequirement, QuoteRequirementType, QuoteStatus, QuoteStatusType, QuoteWorkLine, QuoteWorkSection
from lbrc_services.model.services import Organisation, TaskData, TaskStatusType, ToDo, User, Service, Task, TaskFile
from lbrc_flask.database import db
from lbrc_flask.pytest.faker import UserCreator as BaseUserCreator, FakeCreator, FakeCreatorArgs
from io import BytesIO
from lbrc_flask.forms.dynamic import FieldType
from sqlalchemy import select


class FakerFile():
    def __init__(self, content, filename):
        self.content = content
        self.filename = filename

    def file(self):
        return BytesIO(self.content.encode('utf-8'))

    def file_tuple(self):
        return (
            self.file(),
            self.filename
        )


class UserCreator(BaseUserCreator):
    cls = User


class ServiceCreator(FakeCreator):
    cls = Service

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        name = args.get('name', self.faker.company())

        return Service(
            name=name,
            generic_recipients=args.get('generic_recipients', self.faker.email()),
            field_group=args.get('field_group', self.faker.field_group().get(save=save, name=name)),
            suppress_owner_email=args.get('suppress_owner_email', False),
            introduction=args.get('introduction', self.faker.paragraph(nb_sentences=randint(1,3))),
            description=args.get('description', '\n'.join(self.faker.paragraphs(nb=randint(1,3)))),
            owners=args.get('owners', [])
        )


class OrganisationCreator(FakeCreator):
    cls = Organisation

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        return Organisation(
            name=args.get('name', self.faker.company()),
        )


class TaskCreator(FakeCreator):
    cls = Task

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        name = args.get('name', self.faker.sentence(nb_words=randint(3,10)))

        if (service := args.get('service')) is None:
            service = self.faker.service().get(save=save)
            service_id = None
        else:
            service_id = service.id

        requestor = args.get_or_create('requestor', self.faker.user())
        current_status_type = args.get('current_status_type', TaskStatusType.get_created())
        organisations = args.get('organisations', [self.faker.organisation().get(save=save)])
        organisation_description = args.get('organisation_description', '')
        created_date = args.get('created_date', self.faker.date_time_between(start_date='-1y'))

        return Task(
            name=name,
            service=service,
            service_id=service_id,
            requestor=requestor,
            current_status_type_id=current_status_type.id,
            organisations=organisations,
            organisation_description=organisation_description,
            created_date=created_date,
        )


class QuoteCreator(FakeCreator):
    cls = Quote

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        name = args.get('name', self.faker.sentence(nb_words=randint(3,10)))
        requestor = args.get_or_create('requestor', self.faker.user())
        current_status_type = args.get('current_status_type', QuoteStatusType.get_draft())
        organisation = args.get('organisation', Organisation.get_organisation(Organisation.CARDIOVASCULAR))
        organisation_description = args.get('organisation_description', '')
        quote_price_type = args.get('quote_price_type', QuotePricingType.query.first())
        created_date = args.get('created_date')
        date_requested = args.get('date_requested', datetime.now().date())

        return Quote(
            name=name,
            requestor=requestor,
            current_status_type=current_status_type,
            organisation_id=organisation.id,
            organisation_description=organisation_description,
            quote_pricing_type_id=quote_price_type.id,
            created_date=created_date,
            date_requested=date_requested,
        )


class QuoteStatusCreator(FakeCreator):
    cls = QuoteStatus

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        quote = args.get_or_create('quote', self.faker.quote())
        quote_status_type = args.get('quote_status_type', choice(self._get_quote_status_types()))
        notes = args.get('notes', self.faker.paragraph(nb_sentences=randint(1, 3)))

        return QuoteStatus(
            quote=quote,
            quote_status_type=quote_status_type,
            notes=notes,
        )
    
    @cache
    def _get_quote_status_types(self):
        return list(db.session.execute(select(QuoteStatusType)).scalars())


class QuoteRequirementCreator(FakeCreator):
    cls = QuoteRequirement

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        quote = args.get_or_create('quote', self.faker.quote())
        notes = args.get('notes', self.faker.paragraph(nb_sentences=randint(1, 3)))
        quote_requirement_type = args.get('quote_requirement_type', choice(self._get_quote_requirement_types()))

        return QuoteRequirement(
            quote=quote,
            notes=notes,
            quote_requirement_type=quote_requirement_type,
        )
    
    @cache
    def _get_quote_requirement_types(self):
        return list(db.session.execute(select(QuoteRequirementType)).scalars())


class QuoteWorkSectionCreator(FakeCreator):
    cls = QuoteWorkSection

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        quote = args.get_or_create('quote', self.faker.quote())
        name = args.get('name', self.faker.sentence(nb_words=randint(1,10)))

        return QuoteWorkSection(
            quote=quote,
            name=name,
        )
    

class QuoteWorkLineCreator(FakeCreator):
    cls = QuoteWorkLine

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        quote_work_section = args.get_or_create('quote_work_section', self.faker.quote_work_section())
        name = args.get('name', self.faker.sentence(nb_words=randint(1,10)))
        days = args.get('days', randint(1, 20) * 0.5)

        return QuoteWorkLine(
            quote_work_section=quote_work_section,
            name=name,
            days=days,
        )
    

class TaskFileCreator(FakeCreator):
    cls = TaskFile

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        filename = args.get('filename', self.faker.pystr(min_chars=5, max_chars=10))
        local_filepath = args.get('local_filepath', self.faker.pystr(min_chars=5, max_chars=10))
        task = args.get_or_create('task', self.faker.task())
        field = args.get_or_create('field', self.faker.field())

        return TaskFile(
            filename=filename,
            local_filepath=local_filepath,
            task=task,
            field=field,
        )


class TaskDataCreator(FakeCreator):
    cls = TaskData

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        task = args.get_or_create('task', self.faker.task())
        value = args.get('value', self.faker.pystr(min_chars=5, max_chars=10).upper())

        if (field := args.get('field')) is None:
            field_type_name = choice(FieldType.all_simple_field_types())
            field_type = FieldType._get_field_type(field_type_name)
            field = self.faker.field().get(field_type=field_type)

        return TaskData(
            task=task,
            field=field,
            value=value,
        )


class ToDoCreator(FakeCreator):
    cls = ToDo

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        task = args.get_or_create('task', self.faker.task())
        description = args.get('description', self.faker.paragraph(nb_sentences=randint(1, 3)))
        status = args.get('status')

        return ToDo(
            task=task,
            description=description,
            status=status,
        )


class LbrcServicesProvider(BaseProvider):
    def fake_file(self):
        return FakerFile(self.generator.text(), self.generator.file_name(extension='pdf'))

    @cache
    def user(self):
        return UserCreator(self)

    @cache
    def service(self):
        return ServiceCreator(self)
    
    @cache
    def task(self):
        return TaskCreator(self)

    @cache
    def quote(self):
        return QuoteCreator(self)
    
    @cache
    def quote_status(self):
        return QuoteStatusCreator(self)
    
    @cache
    def quote_requirement(self):
        return QuoteRequirementCreator(self)
    
    @cache
    def quote_work_section(self):
        return QuoteWorkSectionCreator(self)
    
    @cache
    def quote_work_line(self):
        return QuoteWorkLineCreator(self)

    @cache
    def task_file(self):
        return TaskFileCreator(self)
    
    def create_task_file_in_filesystem(self, task_file: TaskFile, fake_file: Optional[FakerFile] = None):
        if fake_file is None:
            fake_file = FakerFile(self.generator.text(), task_file.filename)

        filepath = task_file._new_local_filepath(task_file.filename)
        filepath.parents[0].mkdir(parents=True, exist_ok=True)
        task_file.local_filepath = str(filepath)
        f = open(filepath, "a")
        f.write(fake_file.content)
        f.close()

    @cache
    def task_data(self):
        return TaskDataCreator(self)

    def get_test_field_of_type(self, field_type, choices=None, allowed_file_extensions=None):
        s = self.service().get_in_db()
        f = self.generator.field().get_in_db(field_group=s.field_group, field_type=field_type, choices=choices, allowed_file_extensions='pdf')
        return s,f

    @cache
    def todo(self):
        return ToDoCreator(self)

    @cache
    def organisation(self):
        return OrganisationCreator(self)
